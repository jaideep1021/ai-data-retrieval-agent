"""Reproducible Census country trade panel, 2015–2026 Q2, in USD millions.

Year-sized requests use the documented repeated MONTH/CTY_CODE parameters.
Original response bytes and safe provenance are cached. Missing observations
never become zero; quarterly sums require three valid months for each flow.
"""
import argparse
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.parse
import urllib.request
from census_trade_example import ROOT, load_key

FIELDS={'imports':('GEN_VAL_MO','GEN_VAL_YR'),'exports':('ALL_VAL_MO','ALL_VAL_YR')}
MAPPING=ROOT/'config/africa-census-countries.json'

def parse_batch(raw, flow, year, months, countries):
    """Reject unexpected aggregation, duplicate keys, invalid amounts and dates."""
    data=json.loads(raw);mo,yr=FIELDS[flow]
    required={'CTY_CODE','CTY_NAME','YEAR','MONTH',mo,yr}
    if not isinstance(data,list) or not data or not isinstance(data[0],list):raise ValueError('Invalid response')
    headers=data[0]
    if set(headers) not in (required,required|{'time'}):raise ValueError('Unexpected schema')
    repeated={h for h in headers if headers.count(h)>1}
    if not repeated.issubset({'YEAR','MONTH','CTY_CODE'}):raise ValueError('Unexpected duplicate measure')
    rows=[];seen=set()
    for values in data[1:]:
        if len(values)!=len(headers):raise ValueError('Invalid row width')
        # Census echoes filtered identifiers already requested in get. Accept
        # those copies only when their values agree exactly in every row.
        if any(len({values[i] for i,h in enumerate(headers) if h==key})!=1 for key in repeated):raise ValueError('Conflicting echoed identifiers')
        r=dict(zip(headers,values));code=r['CTY_CODE']
        if code not in countries or r['YEAR']!=str(year) or r['MONTH'] not in {f'{m:02}' for m in months}:raise ValueError('Country or period outside request')
        month=int(r['MONTH']);key=(code,year,month)
        if key in seen:raise ValueError('Duplicate country month')
        if 'time' in r and r['time']!=f'{year}-{month:02}':raise ValueError('Inconsistent time label')
        if not r['CTY_NAME']:raise ValueError('Missing country label')
        seen.add(key)
        def amount(field):
            value=r[field]
            if value is None or value=='':return None
            if not isinstance(value,str) or not re.fullmatch(r'\d+',value):raise ValueError('Invalid dollar measure')
            return int(value)
        rows.append({'country_code':code,'source_country_name':r['CTY_NAME'],'year':year,'month':month,
                     'flow':flow,'monthly_usd':amount(mo),'ytd_usd':amount(yr)})
    return rows

def complete_sum(values, expected):
    """Preserve true zeros; withhold totals when any expected value is absent."""
    return sum(values) if len(values)==expected and all(v is not None for v in values) else None

def millions(value):return None if value is None else str(Decimal(value)/Decimal(1000000))

def build(rows,countries):
    index={}
    for r in rows:
        key=(r['country_code'],r['year'],r['month'],r['flow'])
        if key in index:raise ValueError('Duplicate observation across batches')
        index[key]=r
    quarterly=[];annual=[];checks=[]
    for c in countries:
        code=c['census_code']
        for year in range(2015,2027):
            end=6 if year==2026 else 12
            for q in range(1,end//3+1):
                rec={'country':c['reference_name'],'census_code':code,'year':year,'quarter':q}
                totals={}
                for flow in FIELDS:
                    vals=[index.get((code,year,m,flow),{}).get('monthly_usd') for m in range(q*3-2,q*3+1)]
                    total=complete_sum(vals,3);totals[flow]=total
                    rec[flow+'_usd_millions']=millions(total)
                    rec[flow+'_months_available']=sum(v is not None for v in vals)
                rec['total_trade_usd_millions']=millions(complete_sum(list(totals.values()),2))
                rec['coverage']='COMPLETE' if all(v is not None for v in totals.values()) else 'MISSING_MONTHS'
                quarterly.append(rec)
            rec={'country':c['reference_name'],'census_code':code,'year':year}
            for flow in FIELDS:
                vals=[index.get((code,year,m,flow),{}).get('monthly_usd') for m in range(1,end+1)]
                total=complete_sum(vals,end)
                rec[flow+'_annual_usd_millions']=millions(total) if end==12 else None
                rec[flow+'_in_scope_usd_millions']=millions(total)
                # Check every available cumulative total against monthly sums.
                for month in range(1,end+1):
                    cumulative=complete_sum(vals[:month],month)
                    reported=index.get((code,year,month,flow),{}).get('ytd_usd')
                    checks.append({'country':c['reference_name'],'year':year,'month':month,'flow':flow,
                        'sum_monthly_usd':cumulative,'reported_ytd_usd':reported,
                        'status':'NOT_CHECKABLE' if cumulative is None or reported is None else 'MATCH' if cumulative==reported else 'DIFFERENT'})
            rec['months_in_scope']=end;annual.append(rec)
    return quarterly,annual,checks

def write_csv(path, rows):
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def run():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--folder',type=Path,required=True)
    ap.add_argument('--max-new-requests',type=int,default=24);ap.add_argument('--offline',action='store_true');args=ap.parse_args()
    countries=json.loads(MAPPING.read_text())['countries'];codes={r['census_code'] for r in countries}
    assert len(codes)==14
    args.folder.mkdir(parents=True,exist_ok=True)
    manifest_path=args.folder/'manifest.json'
    manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {'created_utc':datetime.now(timezone.utc).isoformat(),'requests':{},'scope':'2015-01 to 2026-06','units':'USD millions','mapping_sha256':hashlib.sha256(MAPPING.read_bytes()).hexdigest()}
    if manifest['mapping_sha256']!=hashlib.sha256(MAPPING.read_bytes()).hexdigest():raise ValueError('Mapping changed')
    key=None if args.offline else load_key();rows=[];new=0
    for year in range(2015,2027):
        months=list(range(1,7 if year==2026 else 13))
        for flow,(mo,yr) in FIELDS.items():
            ident=f'{year}-{flow}';entry=manifest['requests'].get(ident);rawpath=args.folder/(ident+'.json')
            if entry and entry['status']=='VALIDATED':
                raw=rawpath.read_bytes()
                if hashlib.sha256(raw).hexdigest()!=entry['sha256']:raise ValueError('Cached response changed')
            else:
                if args.offline or new>=args.max_new_requests:continue
                params=[('get',','.join(['CTY_CODE','CTY_NAME','YEAR','MONTH',mo,yr])),('YEAR',str(year))]
                params += [('MONTH',f'{m:02}') for m in months]+[('CTY_CODE',c) for c in sorted(codes)]
                url=f'https://api.census.gov/data/timeseries/intltrade/{flow}/hs?'+urllib.parse.urlencode(params)
                entry={'url_without_key':url,'started_utc':datetime.now(timezone.utc).isoformat(),'status':'STARTED'}
                manifest['requests'][ident]=entry;manifest_path.write_text(json.dumps(manifest,indent=2)+'\n');new+=1
                try:
                    start=time.monotonic()
                    with urllib.request.urlopen(url+'&key='+urllib.parse.quote(key,safe=''),timeout=35) as resp:
                        raw=resp.read(5_000_001);entry['http_status']=resp.status
                    if key.encode() in raw or len(raw)>5_000_000:raise ValueError('Unsafe response')
                    rawpath.write_bytes(raw);entry.update(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),seconds=time.monotonic()-start)
                    if entry['http_status']!=200:raise ValueError('Unexpected HTTP status')
                    result=parse_batch(raw,flow,year,months,codes)
                    entry.update(status='VALIDATED',rows=len(result),completed_utc=datetime.now(timezone.utc).isoformat())
                except (Exception,KeyboardInterrupt) as exc:
                    entry.update(status='FAILED',error_type=type(exc).__name__)
                    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
                    print(ident,'FAILED',type(exc).__name__,flush=True);return 1
                manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
                print(ident,entry['status'],entry['rows'],'rows',flush=True)
            rows+=parse_batch(raw,flow,year,months,codes)
    quarterly,annual,checks=build(rows,countries)
    for name,data in [('monthly',rows),('quarterly',quarterly),('annual',annual),('ytd-checks',checks)]:write_csv(args.folder/(name+'.csv'),data)
    summary={'validated_batches':sum(e['status']=='VALIDATED' for e in manifest['requests'].values()),'new_requests':new,
        'monthly_flow_rows':len(rows),'quarterly_rows':len(quarterly),'complete_quarters':sum(r['coverage']=='COMPLETE' for r in quarterly),
        'ytd_differences':sum(r['status']=='DIFFERENT' for r in checks),'ytd_not_checkable':sum(r['status']=='NOT_CHECKABLE' for r in checks)}
    (args.folder/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
    return 0

if __name__=='__main__':raise SystemExit(run())
