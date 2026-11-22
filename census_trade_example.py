"""One-month Census trade retrieval with secret-free provenance.

Uses the documented country/month query pattern and default national all-goods
aggregation. Do not add a literal commodity TOTAL filter: the development check
returned HTTP 204 for that query. Historical-panel valuation remains provisional.
"""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
FIELDS = {'imports': 'GEN_VAL_MO', 'exports': 'ALL_VAL_MO'}


def parse_response(raw, field, country, period):
    """Require one country-month observation; reject errors, extra rows and nulls."""
    data = json.loads(raw)
    expected = {'CTY_NAME', field, 'time', 'CTY_CODE'}
    if not isinstance(data, list) or len(data) != 2 or not all(isinstance(r,list) for r in data):
        raise ValueError('Expected exactly one data row')
    if len(data[0]) != 4 or set(data[0]) != expected or len(data[1]) != 4:
        raise ValueError('Unexpected response schema or aggregation')
    row = dict(zip(data[0],data[1]))
    if row['CTY_CODE'] != country or row['time'] != period or not row['CTY_NAME']:
        raise ValueError('Response country/period mismatch')
    if not isinstance(row[field],str) or not re.fullmatch(r'\d+',row[field]):
        raise ValueError('Expected nonnegative integer dollar value')
    return {'country_code':country,'country_name':row['CTY_NAME'],'period':period,
            'value_usd':row[field], 'source_field':field,
            'rounded_millions_usd':str((Decimal(row[field])/Decimal(1000000)).quantize(Decimal('0.1'),rounding=ROUND_HALF_UP))}


def load_key():
    """Read a simple .env assignment or environment variable; never print it."""
    key=os.environ.get('CENSUS_API_KEY','').strip()
    if not key and (ROOT/'.env').exists():
        for line in (ROOT/'.env').read_text().splitlines():
            name,sep,value=line.partition('=')
            if sep and name.strip()=='CENSUS_API_KEY':key=value.strip().strip('\"\'')
    if not key:raise ValueError('CENSUS_API_KEY is not configured')
    return key


def run():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--country',default='7910')
    parser.add_argument('--month',default='2020-01')
    args=parser.parse_args()
    if not re.fullmatch(r'\d{4}',args.country) or not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])',args.month):
        parser.error('Expected four-digit Census country code and YYYY-MM')
    key=load_key()
    out=ROOT/'runs'/('census-example-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(parents=True,exist_ok=False)
    manifest={'retrieved_utc':datetime.now(timezone.utc).isoformat(),'requests':[],
              'aggregation':'default country all-goods total; no commodity/district/DF predicate',
              'reference_validated':False,'status':'STARTED'}
    results={}
    try:
        for flow,field in FIELDS.items():
            params={'get':f'CTY_NAME,{field}','time':args.month,'CTY_CODE':args.country}
            url=f'https://api.census.gov/data/timeseries/intltrade/{flow}/hs?'+urllib.parse.urlencode(params)
            entry={'flow':flow,'url_without_key':url};manifest['requests'].append(entry)
            # Never log the authenticated URL, redirect URL, or exception text.
            with urllib.request.urlopen(url+'&key='+urllib.parse.quote(key,safe=''),timeout=30) as response:
                raw=response.read(2_000_001);entry['http_status']=response.status
            if key.encode() in raw:raise ValueError('Credential echoed; response withheld')
            (out/(flow+'.bin')).write_bytes(raw)
            entry.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            if len(raw)>2_000_000 or entry['http_status']!=200:
                raise ValueError('Unexpected size or HTTP status')
            results[flow]=parse_response(raw,field,args.country,args.month)
        results['total_trade_usd']=str(sum(int(results[f]['value_usd']) for f in FIELDS))
        (out/'result.json').write_text(json.dumps(results,indent=2)+'\n')
        manifest['status']='RETRIEVED_NOT_HISTORICALLY_VALIDATED'
        print(json.dumps(results,indent=2))
    except Exception as exc:
        manifest.update(status='FAILED',error_type=type(exc).__name__)
        print('Retrieval failed:',type(exc).__name__,'— inspect the private manifest.')
    finally:
        (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        print('Evidence:',out)
    return 0 if manifest['status']!='FAILED' else 1

if __name__=='__main__':
    raise SystemExit(run())
