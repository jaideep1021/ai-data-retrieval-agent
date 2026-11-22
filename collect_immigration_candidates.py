"""Collect country-of-birth ACS estimates as a separately labelled alternative.

This does not claim replication of the reference Immigration field. One-year
ACS data stay annual; regional totals are never assigned to individual countries.
"""
import csv,json,hashlib,re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlencode,quote
from census_trade_example import ROOT,load_key
ALIASES={'Cape Verde':['Cabo Verde','Cape Verde'],"Cote d'Ivoire":['Ivory Coast',"Cote d'Ivoire"]}

def codes_for(variables,countries):
    result={}
    for country in countries:
        names=ALIASES.get(country,[country]);found=[]
        for code,item in variables.items():
            label=item.get('label','')
            if re.fullmatch(r'B05006_\d{3}E',code) and 'Africa' in [part.rstrip(':') for part in label.split('!!')] and label.split('!!')[-1].rstrip(':') in names:
                found.append(code)
        if len(found)>1:raise ValueError('Ambiguous country mapping')
        if found:result[country]=found[0]
    return result

def parse_value(value):
    if value is None:return None,'MISSING'
    if not isinstance(value,str) or not re.fullmatch(r'-?\d+',value):raise ValueError('Invalid estimate')
    n=int(value)
    return (n,'AVAILABLE') if n>=0 else (None,'SOURCE_SENTINEL_'+str(n))

def fetch(folder,name,url,key=None):
    path=folder/(name+'.json');meta={'url':url,'retrieved_utc':datetime.now(timezone.utc).isoformat()}
    if path.exists():
        old=json.loads((folder/(name+'-request.json')).read_text())
        raw=path.read_bytes()
        if old['url']!=url or hashlib.sha256(raw).hexdigest()!=old.get('sha256'):
            raise ValueError('Cached source mismatch')
        return json.loads(raw),old
    try:
        authenticated=url+('&key='+quote(key,safe='') if key else '')
        with urlopen(authenticated,timeout=25) as r:raw=r.read(5_000_001)
        if len(raw)>5_000_000:raise ValueError('Oversize response')
        if key and key.encode() in raw:raise ValueError('Credential echoed')
        path.write_bytes(raw);meta.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        payload=json.loads(raw);meta['status']='DOWNLOADED';return payload,meta
    except Exception as e:
        meta.update(status='ACCESS_FAILED',error_type=type(e).__name__);return None,meta
    finally:
        (folder/(name+'-request.json')).write_text(json.dumps(meta,indent=2)+'\n')

def run(folder):
    folder.mkdir(parents=True,exist_ok=True)
    countries=[r['reference_name'] for r in json.loads((ROOT/'config/africa-census-countries.json').read_text())['countries']]
    key=load_key()
    def year_job(year):
        base=f'https://api.census.gov/data/{year}/acs/acs1'
        data,meta=fetch(folder,f'{year}-metadata',base+'/groups/B05006.json')
        mapping=codes_for(data['variables'],countries) if data else {}
        result=None
        if data:
            fields=['NAME']+[v for code in mapping.values() for v in (code,code[:-1]+'M')]
            result,meta=fetch(folder,f'{year}-data-v2' if year==2015 else f'{year}-data',base+'?'+urlencode({'get':','.join(fields),'for':'us:*'}),key)
        parsed={}
        if result:
            if len(result)!=2 or len(result[0])!=len(set(result[0])) or len(result[0])!=len(result[1]):raise ValueError('Unexpected national data')
            parsed=dict(zip(*result))
            if parsed.get('us')!='1' or parsed.get('NAME')!='United States':raise ValueError('Wrong geography')
            if any(code not in parsed or code[:-1]+'M' not in parsed for code in mapping.values()):raise ValueError('Missing requested fields')
        rows=[]
        for c in countries:
            code=mapping.get(c);value=moe=None;status='ACCESS_FAILED'
            if data and code is None:status='COUNTRY_NOT_SEPARATELY_TABULATED'
            elif parsed:
                value,status=parse_value(parsed[code]);moe,moestatus=parse_value(parsed[code[:-1]+'M'])
            rows.append({'country':c,'year':year,'estimate_persons':value,'margin_of_error_persons':moe,
                         'status':status,'source_variable':code,'source':'ACS 1-year B05006','mapping':'ALTERNATIVE_NOT_REFERENCE_VALIDATED'})
        return rows
    years=[2015,2019,2021,2022,2023,2024,2025]
    with ThreadPoolExecutor(max_workers=3) as pool:rows=[r for result in pool.map(year_job,years) for r in result]
    for year,status in [(2020,'STANDARD_ACS1_NOT_RELEASED'),(2026,'YEAR_NOT_COMPLETE')]:
        rows += [{'country':c,'year':year,'estimate_persons':None,'margin_of_error_persons':None,'status':status,'source_variable':None,'source':'ACS 1-year B05006','mapping':'ALTERNATIVE_NOT_REFERENCE_VALIDATED'} for c in countries]
    rows.sort(key=lambda r:(r['country'],r['year']))
    with (folder/'annual-candidates.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    summary={str(y):{s:sum(r['year']==y and r['status']==s for r in rows) for s in sorted({r['status'] for r in rows})} for y in sorted({r['year'] for r in rows})}
    (folder/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);run(p.parse_args().folder)
