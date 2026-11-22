"""Bounded 2015 Q1 check: two countries, two flows, three months (12 requests).

Uses the existing validated monthly parser. Saves response bytes and secret-free
provenance. A quarter is summed only when all three monthly requests succeed.
This diagnostic does not change reference values or establish field semantics.
"""
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request
from census_trade_example import ROOT, FIELDS, load_key, parse_response

COUNTRIES = {'Angola':'7620','South Africa':'7910'}
MONTHS = ('2015-01','2015-02','2015-03')

def sum_complete_quarter(records):
    if len(records)!=3 or {r['period'] for r in records}!=set(MONTHS):
        raise ValueError('Quarter requires exactly three distinct months')
    if len({r['country_code'] for r in records})!=1 or len({r['source_field'] for r in records})!=1:
        raise ValueError('Mixed countries or trade flows')
    return sum(int(r['value_usd']) for r in records)

def run():
    key=load_key()
    out=ROOT/'runs'/('census-quarter-check-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(parents=True,exist_ok=False)
    manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'request_limit':12,'requests':[],
        'scope':'2015 Q1, Angola and South Africa, country totals, default all goods and transport modes'}
    totals=[]
    for country,code in COUNTRIES.items():
        for flow,field in FIELDS.items():
            records=[]
            for period in MONTHS:
                params={'get':f'CTY_NAME,{field}','time':period,'CTY_CODE':code}
                url=f'https://api.census.gov/data/timeseries/intltrade/{flow}/hs?'+urllib.parse.urlencode(params)
                name=f'{code}-{flow}-{period}.json'
                entry={'country':country,'flow':flow,'period':period,'url_without_key':url}
                manifest['requests'].append(entry)
                try:
                    with urllib.request.urlopen(url+'&key='+urllib.parse.quote(key,safe=''),timeout=25) as resp:
                        raw=resp.read(2_000_001);entry['http_status']=resp.status
                    if key.encode() in raw:raise ValueError('Credential echoed')
                    if len(raw)>2_000_000:raise ValueError('Response too large')
                    (out/name).write_bytes(raw)
                    entry.update(raw_file=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
                    if entry['http_status']!=200:raise ValueError('Unexpected HTTP status')
                    parsed=parse_response(raw,field,code,period);records.append(parsed);entry['status']='VALIDATED'
                except Exception as exc:
                    # Never record authenticated URLs or exception messages.
                    entry.update(status='FAILED',error_type=type(exc).__name__)
                (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
                print(country,flow,period,entry['status'],flush=True)
            if len(records)==3:
                total=sum_complete_quarter(records)
                totals.append({'country':country,'country_code':code,'flow':flow,'quarter':'2015 Q1',
                    'source_field':field,'total_usd':str(total),'total_usd_millions':str(Decimal(total)/Decimal(1000000)),
                    'monthly':records})
    (out/'quarter-totals.json').write_text(json.dumps(totals,indent=2)+'\n')
    manifest['complete_quarter_flows']=len(totals)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('OUTPUT',out,flush=True)
    print(json.dumps([{k:v for k,v in r.items() if k!='monthly'} for r in totals],indent=2))
    return 0 if len(totals)==4 else 1

if __name__=='__main__':raise SystemExit(run())
