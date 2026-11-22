"""Offline reconciliation and workbook inputs for the Census panel.

Independently checks the monthly dollar totals against quarterly CSVs, earlier
live observations and the unchanged reference. Comparison is diagnostic only:
legacy sample dates are not assumed reliable and no values are overwritten.
"""
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from census_trade_example import ROOT, load_key

def read(path):
    with path.open(newline='') as f:return list(csv.DictReader(f))

def run(folder):
    manifest=json.loads((folder/'manifest.json').read_text());monthly=read(folder/'monthly.csv')
    quarters=read(folder/'quarterly.csv');annual=read(folder/'annual.csv');checks=read(folder/'ytd-checks.csv')
    assert len(quarters)==644 and len({(r['census_code'],r['year'],r['quarter']) for r in quarters})==644
    assert len(monthly)==3864 and len({(r['country_code'],r['year'],r['month'],r['flow']) for r in monthly})==3864
    for e in manifest['requests'].values():
        assert e['status']=='VALIDATED'
    for ident,e in manifest['requests'].items():assert hashlib.sha256((folder/(ident+'.json')).read_bytes()).hexdigest()==e['sha256']
    index={(r['country_code'],int(r['year']),int(r['month']),r['flow']):r for r in monthly}
    for r in quarters:
        values=[]
        for flow in ['imports','exports']:
            observations=[index[(r['census_code'],int(r['year']),m,flow)]['monthly_usd'] for m in range(int(r['quarter'])*3-2,int(r['quarter'])*3+1)]
            if any(v=='' for v in observations):assert r[flow+'_usd_millions']=='';continue
            exact=sum(int(v) for v in observations);assert Decimal(r[flow+'_usd_millions'])==Decimal(exact)/1000000;values.append(exact)
        if len(values)==2:assert Decimal(r['total_trade_usd_millions'])==Decimal(sum(values))/1000000
    prior=json.loads((ROOT/'runs/census-quarter-check-20261119T194910134915Z/quarter-totals.json').read_text())
    for t in prior:
        for old in t['monthly']:
            actual=index[(old['country_code'],2015,int(old['period'][-2:]),t['flow'])]
            assert actual['monthly_usd']==old['value_usd']
    refdir=ROOT/'runs/trade-field-review-20261119T154259777907Z'
    provenance=json.loads((refdir/'manifest.json').read_text())
    assert hashlib.sha256(Path(provenance['reference_path']).read_bytes()).hexdigest()==provenance['reference_sha256']
    refs=json.loads((refdir/'reference-trade-values.json').read_text())
    qidx={(r['country'],int(r['year']),int(r['quarter'])):r for r in quarters};aidx={(r['country'],int(r['year'])):r for r in annual}
    comparison=[];matches={k:0 for k in ['IQ','EQ','IYR','EYR']}
    for r in refs:
        q=qidx[(r['CTYNAME'],r['year'],r['quarter'])];a=aidx[(r['CTYNAME'],r['year'])]
        row={'country':r['CTYNAME'],'year':r['year'],'quarter':r['quarter']}
        for field,value in [('IQ',q['imports_usd_millions']),('EQ',q['exports_usd_millions']),('IYR',a['imports_annual_usd_millions']),('EYR',a['exports_annual_usd_millions'])]:
            row['reference_'+field]=r[field];row['census_'+field+'_millions']=value
            # Numeric closeness is reported only; not a claim of semantic validation.
            diff=Decimal(value)-Decimal(str(r[field])) if value!='' else None
            row['difference_'+field]=str(diff) if diff is not None else None
            if diff is not None and abs(diff)<=Decimal('0.001'):matches[field]+=1
        comparison.append(row)
    from census_trade_panel import write_csv
    write_csv(folder/'reference-comparison.csv',comparison)
    labels={}
    for r in monthly:labels.setdefault(r['country_code'],set()).add(r['source_country_name'])
    summary={'quarterly_rows':len(quarters),'historical_rows':280,'extension_rows':364,'monthly_flow_rows':len(monthly),
        'complete_quarters':sum(r['coverage']=='COMPLETE' for r in quarters),'ytd_check_counts':{s:sum(r['status']==s for r in checks) for s in ['MATCH','DIFFERENT','NOT_CHECKABLE']},
        'prior_monthly_checks':12,'reference_close_within_0_001_million':matches,
        'observed_country_labels':{k:sorted(v) for k,v in labels.items()},'reference_unchanged':True}
    # Do not put API credentials in exported data, logs, or provenance.
    secret=load_key().encode()
    assert all(secret not in p.read_bytes() for p in folder.iterdir() if p.is_file())
    (folder/'validation.json').write_text(json.dumps(summary,indent=2)+'\n')
    def typed(rows,text):
        return [{k:(None if v=='' or v is None else v if k in text else float(v)) for k,v in r.items()} for r in rows]
    payload={'sheets':[
        {'name':'Quarterly trade','rows':typed(quarters,{'country','census_code','coverage'})},
        {'name':'Annual and partial year','rows':typed(annual,{'country','census_code'})},
        {'name':'Reference comparison','rows':typed(comparison,{'country'})}], 'validation':summary}
    (folder/'workbook-data.json').write_text(json.dumps(payload,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);run(p.parse_args().folder)
