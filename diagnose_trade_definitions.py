"""Bounded historical definition diagnostic, never an automatic reference repair.

Six requests: three countries x two flows, monthly 2013–2019. Preserves raw bytes
and metadata, tests named Census measures; no arbitrary fitted scale factors.
"""
from datetime import datetime, timezone
from collections import defaultdict
from decimal import Decimal
import json, hashlib, re, urllib.parse, urllib.request
from census_trade_example import ROOT, load_key

FIELDS = {
 'imports':['GEN_VAL_MO','GEN_VAL_YR','CON_VAL_MO','CON_VAL_YR','GEN_CIF_MO','GEN_CIF_YR','AIR_VAL_MO','AIR_VAL_YR'],
 'exports':['ALL_VAL_MO','ALL_VAL_YR','AIR_VAL_MO','AIR_VAL_YR']}
COUNTRIES={'Angola':'7620','South Africa':'7910','Nigeria':'7530'}

def parse(raw, fields, code):
    values=json.loads(raw); expected=set(fields)|{'CTY_NAME','CTY_CODE','time'}
    if not isinstance(values,list) or len(values)<2 or set(values[0])!=expected or len(values[0])!=len(expected):
        raise ValueError('Schema mismatch')
    rows=[];seen=set()
    for vals in values[1:]:
        if len(vals)!=len(values[0]):raise ValueError('Malformed row')
        r=dict(zip(values[0],vals));t=r['time']
        if r['CTY_CODE']!=code or not re.fullmatch(r'201[3-9]-(0[1-9]|1[0-2])',t) or t in seen:
            raise ValueError('Unexpected country, date or duplicate')
        if any(not isinstance(r[f],str) or not re.fullmatch(r'\d+',r[f]) for f in fields):
            raise ValueError('Missing or invalid measure')
        seen.add(t);rows.append(r)
    if len(rows)!=84:raise ValueError('Incomplete 2013–2019 monthly series')
    return sorted(rows,key=lambda r:r['time'])

def retrieve():
    key=load_key();out=ROOT/'runs'/('trade-definition-diagnostic-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir(parents=True)
    manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'requests':[],'request_limit':6}
    for name,code in COUNTRIES.items():
        for flow,fields in FIELDS.items():
            url=f'https://api.census.gov/data/timeseries/intltrade/{flow}/hs?'+urllib.parse.urlencode({'get':','.join(['CTY_NAME',*fields]),'CTY_CODE':code,'time':'from 2013-01 to 2019-12'})
            e={'country':name,'code':code,'flow':flow,'url_without_key':url};manifest['requests'].append(e)
            e['status']='STARTED'
            (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
            try:
                with urllib.request.urlopen(url+'&key='+urllib.parse.quote(key,safe=''),timeout=40) as response:raw=response.read(2_000_001);e['http_status']=response.status
                if len(raw)>2_000_000 or key.encode() in raw:raise ValueError('Unsafe response')
                filename=f'{code}-{flow}.json';(out/filename).write_bytes(raw);e.update(raw_file=filename,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
                if e['http_status']!=200:raise ValueError('Unexpected status')
                rows=parse(raw,fields,code);e.update(status='VALIDATED',rows=len(rows))
            except KeyboardInterrupt:
                e.update(status='INTERRUPTED',error_type='KeyboardInterrupt')
                (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
                return out
            except Exception as exc:e.update(status='FAILED',error_type=type(exc).__name__)
            (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
            print(name,flow,e['status'],flush=True)
            if e['status']=='FAILED':
                print('Stopped after first failed request; review before retrying.',flush=True)
                return out
    print('OUTPUT',out,flush=True)
    return out

if __name__=='__main__':retrieve()
