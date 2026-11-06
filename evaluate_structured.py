"""Paired structured-service experiments with an explicit freeze for held-out data.

Run never opens references. Score is an offline operation on saved results.
Socrata is a specialized public-data catalog/API, not a general web search engine.
No Gemini calls are used in this schema-guided experiment.
"""
import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import time

from dotenv import load_dotenv
import serpapi

from business_agent import decimal_value, save_json
from evaluate_business import load_inputs
from search_providers import SearchProvider
from structured_retrieval import run, VERSION

SOURCES=['structured_retrieval.py','evaluate_structured.py','business_agent.py','business_documents.py',
         'autonomous.py','search_providers.py','requirements.txt','requirements-business.txt']
PROVIDERS=['serpapi','brave','socrata']


def hashes():
    return {name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in SOURCES}


def execute(inputs,output,split,freeze=None):
    tasks=load_inputs(inputs)
    selected=[t for t in tasks if (int(t['record_id'].split('-')[-1])<=6)==(split=='development')]
    if split=='evaluation':
        if freeze is None:raise ValueError('Held-out evaluation requires an explicit freeze file')
        frozen=json.loads(freeze.read_text())
        if frozen['source_hashes']!=hashes() or frozen['input_sha256']!=hashlib.sha256(inputs.read_bytes()).hexdigest():
            raise ValueError('Implementation/input differs from the frozen protocol')
    load_dotenv('.env',override=False)
    if not os.getenv('SERPAPI_KEY') or not os.getenv('BRAVE_SEARCH_API_KEY'):raise ValueError('Search credentials missing')
    output.mkdir(parents=True,exist_ok=False)
    snapshot=output/'source-snapshot';snapshot.mkdir()
    for name in SOURCES:shutil.copy2(name,snapshot/name)
    manifest={'version':VERSION,'split':split,'started_at':datetime.now(timezone.utc).isoformat(),
              'source_hashes':hashes(),'input_sha256':hashlib.sha256(inputs.read_bytes()).hexdigest(),
              'planned_trials':len(selected)*3,'completed_trials':0,'artifacts':[],
              'model_calls':0,'status':'RUNNING','query_generation':'DETERMINISTIC_DOMAIN_TEMPLATE',
              'limits':{'searches_or_catalog_queries':2,'metadata_reads':4,'link_page_reads':3}}
    save_json(output/'manifest.json',manifest)
    services={'serpapi':SearchProvider('serpapi',client=serpapi.Client(api_key=os.environ['SERPAPI_KEY'],timeout=20)),
              'brave':SearchProvider('brave',key=os.environ['BRAVE_SEARCH_API_KEY']),'socrata':'socrata'}
    try:
        for i,task in enumerate(selected):
            order=PROVIDERS[i%3:]+PROVIDERS[:i%3]
            for provider in order:
                name=task['record_id']+'-'+provider
                result=run(task,services[provider],output/name)
                manifest['artifacts'].append(name);manifest['completed_trials']+=1
                save_json(output/'manifest.json',manifest)
                print(f'{manifest["completed_trials"]}/{manifest["planned_trials"]} {name}: {result["decision"]}',flush=True)
                if result.get('stop_batch'):
                    manifest.update(status='STOPPED',stop_reason=result.get('error_type'));return
        manifest['status']='COMPLETE'
    except BaseException as exc:
        manifest.update(status='INTERRUPTED',error_type=type(exc).__name__);raise
    finally:
        manifest['ended_at']=datetime.now(timezone.utc).isoformat();save_json(output/'manifest.json',manifest)


def score_trial(result,ref):
    index=result.get('candidate_source_index')
    source=result['sources'][index] if index is not None else None
    value=source.get('value') if source else None
    def correct(v):
        return v is not None and abs(decimal_value(v)-Decimal(ref['expected']))<=Decimal(ref['absolute_tolerance'])
    requests=result['requests'];searches=sum(r['kind']=='search' for r in requests)
    api=sum(r['kind'] in ('catalog','metadata','rows') for r in requests)
    accepted=result.get('authority_policy')=='ACCEPT_AUTHORITATIVE_RECORD'
    cost=searches*({'serpapi':.025,'brave':.005}.get(result['provider'],0))
    return {'record_id':result['input']['record_id'],'provider':result['provider'],'split':ref['split'],
            'attribute':result['input']['attribute'],'condition':result['input']['condition'],'candidate':value,
            'correct':bool(correct(value) and source and source['context_match']),
            'retrieved':any(s.get('status')=='RETRIEVED' for s in result['sources']),
            'accepted':accepted,'accepted_correct':bool(accepted and correct(result.get('accepted_value'))),
            'agreement_policy':result.get('agreement_policy','ERROR'),
            'authority_policy':result.get('authority_policy','ERROR'),'error_type':result.get('error_type'),
            'seconds':result['seconds'],'search_attempts':searches,'public_api_attempts':api,
            'search_cost_scenario_usd':cost,'model_calls':0,'billing_verified':False}


def summarize(rows):
    result={}
    for provider in PROVIDERS:
        items=[r for r in rows if r['provider']==provider]
        if not items:continue
        n=len(items);accepted=sum(r['accepted'] for r in items);correct=sum(r['correct'] for r in items)
        ac=sum(r['accepted_correct'] for r in items)
        result[provider]={'n':n,'correct':correct,'accuracy':correct/n,'retrieved':sum(r['retrieved'] for r in items),
            'accepted':accepted,'accepted_correct':ac,'incorrect_accepted':accepted-ac,
            'accepted_precision':ac/accepted if accepted else None,'unresolved_rate':1-accepted/n,
            'agreement_accepted':sum(r['agreement_policy']=='AGREEMENT_OBSERVED' for r in items),
            'mean_seconds':statistics.mean(r['seconds'] for r in items),'median_seconds':statistics.median(r['seconds'] for r in items),
            'search_attempts':sum(r['search_attempts'] for r in items),'public_api_attempts':sum(r['public_api_attempts'] for r in items),
            'search_cost_scenario_usd':sum(r['search_cost_scenario_usd'] for r in items)}
    return result


def score(output,references):
    manifest=json.loads((output/'manifest.json').read_text())
    saved=[json.loads((output/name/'result.json').read_text()) for name in manifest['artifacts']]
    refs={r['record_id']:r for r in json.loads(references.read_text())['cases']}
    rows=[score_trial(r,refs[r['input']['record_id']]) for r in saved]
    result={'run_status':manifest['status'],'planned_trials':manifest['planned_trials'],'attempted_trials':len(rows),
            'unrun_trials':manifest['planned_trials']-len(rows),'observations':rows,'summary':summarize(rows),
            'reference_sha256':hashlib.sha256(references.read_bytes()).hexdigest(),
            'cost_note':'Search allocation scenario, not invoice. Public API calls are counted separately; no model calls.',
            'query_generation':'DETERMINISTIC_DOMAIN_TEMPLATE'}
    save_json(output/'scored-results.json',result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['run','score','freeze'])
    parser.add_argument('--inputs',type=Path,default=Path('examples/week3/agent-inputs.json'))
    parser.add_argument('--references',type=Path,default=Path('examples/week3/evaluator-manifest.json'))
    parser.add_argument('--split',choices=['development','evaluation'],default='development')
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--freeze',type=Path)
    args=parser.parse_args()
    if args.action=='run':execute(args.inputs,args.output_dir,args.split,args.freeze)
    elif args.action=='score':print(json.dumps(score(args.output_dir,args.references)['summary'],indent=2))
    else:
        manifest=json.loads((args.output_dir/'manifest.json').read_text())
        if manifest['status']!='COMPLETE' or manifest['split']!='development':raise ValueError('Complete development run required')
        if manifest['source_hashes']!=hashes():raise ValueError('Development run does not match current code')
        destination=args.output_dir/'freeze.json'
        if destination.exists():raise ValueError('Freeze already exists')
        save_json(destination,{'source_hashes':hashes(),'input_sha256':manifest['input_sha256'],
                               'created_at':datetime.now(timezone.utc).isoformat(),'development_run':args.output_dir.name})


if __name__=='__main__':main()
