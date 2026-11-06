"""Experimental schema-guided retrieval; no answer key or fixed dataset ID.

Discover datasets using a search service, inspect their published schema, query
one exact market/quarter record, and compare conservative versus authority-aware
verification. Query construction is deterministic and domain-specific, not LLM
query generation. This distinction must remain explicit in experiment reports.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urlencode, urlsplit

from business_agent import BusinessInput, BusinessRetriever, decimal_value, save_json
from search_providers import SearchServiceError


class APIStop(Exception):
    """Stop on access/quota failures; never repeatedly consume blocked calls."""

CATALOG = 'https://api.us.socrata.com/api/catalog/v1'
VERSION = 'week3-structured-dev2'
FIELDS = ('year','quarter','citymarketid_1','citymarketid_2','city1','city2','fare','passengers','nsmiles')


def dataset_location(url):
    """Recognize a discovered Socrata-style identifier, not a preselected one."""
    parts=urlsplit(url)
    if parts.scheme!='https' or not parts.hostname or parts.username or parts.password:
        return None
    match=re.search(r'(?:^|/)([a-z0-9]{4}-[a-z0-9]{4})(?:/|\.|$)',parts.path)
    return (parts.hostname,match[1]) if match else None


def authority(metadata, host):
    """Explicit DOT trust registry plus independent metadata conditions.

    The registry is a declared domain-specific trust assumption, not discovered
    proof of authority. A .gov suffix or model opinion alone is insufficient.
    Community views and absent attribution are rejected. This is not signature
    verification and cannot establish that an official publisher is error-free.
    """
    link=urlsplit(metadata.get('attributionLink') or '')
    conditions={
        'registered_publisher_host':host in {'data.transportation.gov','datahub.transportation.gov','data.bts.gov'},
        'official_provenance':metadata.get('provenance')=='official',
        'named_publisher':'department of transportation' in (metadata.get('attribution') or '').lower(),
        'publisher_link':link.scheme=='https' and link.hostname in {'www.transportation.gov','transportation.gov','www.bts.gov','bts.gov'},
    }
    return {'classification':'ORIGINAL_PUBLISHER' if all(conditions.values()) else 'UNCONFIRMED_OR_SECONDARY',
            'checks':conditions,'attribution':metadata.get('attribution'),'attribution_link':metadata.get('attributionLink')}


def valid_schema(metadata):
    """This adapter deliberately supports the declared city-market schema only."""
    if re.search(r'airport.*pair',metadata.get('name',''),re.I):return False
    columns={c.get('fieldName'):c for c in metadata.get('columns',[])}
    if not set(FIELDS)<=set(columns):return False
    return ('market' in columns['citymarketid_1'].get('description','').lower()
            and 'day' in columns['passengers'].get('description','').lower()
            and 'mile' in columns['nsmiles'].get('description','').lower()
            and 'overall' in columns['fare'].get('description','').lower())


def row_query(task):
    """Question identifiers filter rows; no candidate value enters the query."""
    a,b=task['citymarketid_1'],task['citymarketid_2']
    if not a.isdigit() or not b.isdigit():raise ValueError('Invalid market identifiers')
    return {'$where':f"year={task['year']} AND quarter={task['quarter']} AND ((citymarketid_1={a} AND citymarketid_2={b}) OR (citymarketid_1={b} AND citymarketid_2={a}))",'$limit':2,'$select':','.join(FIELDS)}


def context_valid(row,task):
    try:
        return (int(row['year'])==task['year'] and int(row['quarter'])==task['quarter']
            and {str(row['citymarketid_1']),str(row['citymarketid_2'])}=={task['citymarketid_1'],task['citymarketid_2']}
            and decimal_value(str(row[task['attribute']]))>=0)
    except (KeyError,ValueError,TypeError):return False


def verify(sources):
    """Replay both policies on identical evidence; copies are not independent."""
    usable=[s for s in sources if s.get('context_match')]
    values={decimal_value(s['value']) for s in usable}
    conflict=len(values)>1
    old=('CONFLICT' if conflict else 'INSUFFICIENT_EVIDENCE' if len(usable)<2 else
         'DUPLICATE_EVIDENCE' if len({s.get('row_sha256') for s in usable})<2 else 'AGREEMENT_OBSERVED')
    authoritative=[s for s in usable if s['authority']['classification']=='ORIGINAL_PUBLISHER']
    new='CONFLICT' if conflict else ('ACCEPT_AUTHORITATIVE_RECORD' if authoritative else 'UNRESOLVED')
    return {'agreement_policy':old,'authority_policy':new,
            'accepted_value':authoritative[0]['value'] if new=='ACCEPT_AUTHORITATIVE_RECORD' else None,
            'independence':'NOT_ESTABLISHED','policy_status':'EXPERIMENTAL_DOMAIN_SPECIFIC'}


def run(task, provider, output, fetcher=None):
    """Two searches, at most four metadata reads and three link-page reads.

    Socrata catalog is a third discovery service. SerpApi/Brave use their normal
    search results and the same downstream schema adapter. All API requests and
    source bytes are recorded; expected values are unavailable to this function.
    """
    task=BusinessInput.model_validate(task).model_dump()
    if task['unit']!={'fare':'USD','passengers':'passenger trips/day','nsmiles':'miles'}[task['attribute']]:
        raise ValueError('Unit contradicts declared DOT schema contract')
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    own=fetcher is None;fetcher=fetcher or BusinessRetriever()
    started=time.perf_counter()
    result={'version':VERSION,'input':task,'provider':provider if isinstance(provider,str) else provider.name,
            'reference_used':False,'unit_basis':'DECLARED_DOT_SCHEMA_CONTRACT','queries':[],'requests':[],'sources':[],'discovery':[], 'decision':'ERROR'}
    def get(url, label):
        tick=time.perf_counter();record={'url':url,'kind':label};result['requests'].append(record)
        try:
            # Documented API access is separate from webpage crawling. Keep public
            # destination/redirect/size limits; never bypass HTTP access errors.
            time.sleep(1)
            record['access_mode']='DOCUMENTED_PUBLIC_API'
            status,kind,body,final=fetcher.read(url,check_robots=False)
            if status in (401,403,429):
                record['http_status']=status
                raise APIStop()
            record.update(http_status=status,final_url=final)
            if status!=200:raise ValueError('Non-success status')
            raw=body if isinstance(body,bytes) else body.encode()
            digest=hashlib.sha256(raw).hexdigest();name=f'{len(result["requests"]):02d}-{label}-{digest[:12]}.txt'
            (output/name).write_bytes(raw);record.update(evidence_file=name,sha256=digest)
            return json.loads(raw)
        finally:record['seconds']=time.perf_counter()-tick
    try:
        queries=['quarterly city pair airfare passenger distance open dataset',
                 f"historical city market {task['attribute']} {task['year']} quarterly data download"]
        candidates=[];seen=set();pages=0;metadata_reads=0
        for query in queries:
            result['queries'].append(query)
            if isinstance(provider,str):
                if provider!='socrata':raise ValueError('Unknown catalog')
                response=get(CATALOG+'?'+urlencode({'q':query,'limit':10}),'catalog')
                found=[{'url':x['link'],'title':x.get('resource',{}).get('name','')} for x in response.get('results',[]) if x.get('link')]
            else:
                tick=time.perf_counter();attempt={'kind':'search','provider':provider.name,'query':query,'status':'error'}
                result['requests'].append(attempt)
                try:
                    found=provider.search(query);attempt.update(status='ok',results=found)
                finally:attempt['seconds']=time.perf_counter()-tick
            candidates.extend(found)
            cursor=0
            while cursor<len(candidates):
                candidate=candidates[cursor];cursor+=1
                url=candidate['url']
                if url in seen:continue
                seen.add(url);result['discovery'].append(candidate)
                location=dataset_location(url)
                if not location:
                    if pages>=3:continue
                    pages+=1
                    try:
                        document=fetcher.fetch_document(url)
                        # Record the actual page proving every followed link.
                        name=f'discovery-page-{pages}.txt';(output/name).write_text(document['text'])
                        result['requests'].append({'kind':'link_page','url':url,'final_url':document['final_url'],
                            'evidence_file':name,'sha256':hashlib.sha256(document['text'].encode()).hexdigest()})
                        linked=[{**x,'parent':url} for x in document['links'] if dataset_location(x['url'])]
                        candidates.extend(linked)
                    except Exception as exc:
                        result['requests'].append({'kind':'link_page','url':url,'error_type':type(exc).__name__})
                    continue
                if metadata_reads>=4:continue
                metadata_reads+=1;host,identifier=location
                source={'url':url,'host':host,'dataset_id':identifier,'status':'ERROR'};result['sources'].append(source)
                try:
                    metadata=get(f'https://{host}/api/views/{identifier}.json','metadata')
                    metadata_host=urlsplit(result['requests'][-1]['final_url']).hostname
                    source['authority']=authority(metadata,metadata_host)
                    if not valid_schema(metadata):source['status']='SCHEMA_MISMATCH';continue
                    rows=get(f'https://{host}/resource/{identifier}.json?'+urlencode(row_query(task)),'rows')
                    if not isinstance(rows,list) or len(rows)!=1:source['status']='ABSENT_OR_AMBIGUOUS';continue
                    row=rows[0]
                    same_origin=urlsplit(result['requests'][-1]['final_url']).hostname==metadata_host
                    source['authority']['checks']['record_origin_matches_metadata']=same_origin
                    if not same_origin:source['authority']['classification']='UNCONFIRMED_OR_SECONDARY'
                    source['row_sha256']=result['requests'][-1]['sha256'];source.update(row=row,context_match=context_valid(row,task),value=str(row.get(task['attribute'],'')),
                        status='RETRIEVED',field_metadata={c['fieldName']:c.get('description') for c in metadata['columns'] if c.get('fieldName') in FIELDS})
                except APIStop:raise
                except Exception as exc:source['error_type']=type(exc).__name__
            if any(s.get('context_match') for s in result['sources']):break
        result.update(verify(result['sources']));result['decision']=result['authority_policy']
        result['candidate_source_index']=next((i for i,s in enumerate(result['sources']) if s.get('context_match')),None)
    except Exception as exc:
        result['error_type']=type(exc).__name__
        result['stop_batch']=isinstance(exc,APIStop) or isinstance(exc,SearchServiceError)
    finally:
        result['seconds']=time.perf_counter()-started
        result['robots_checks']=fetcher.policy_events
        save_json(output/'result.json',result)
        if own:fetcher.session.close()
    return result
