"""Diagnose distance definitions and derive other-country seats without imputation.

All distance methods are hypotheses in miles. Comparisons are descriptive, not
an automatic model-selection procedure. Empty groups and zero-weight groups
remain missing. No existing workbook is modified.
"""
import csv,io,json,hashlib,zipfile
from collections import defaultdict,Counter
from pathlib import Path
import xlrd
from worldbank_panel import ROOT
from validate_worldbank_panel import REFERENCE_HASH

def distance_candidates(rows):
    if not rows:return {}
    d=[float(r['DISTANCE']) for r in rows]
    result={'row_mean':sum(d)/len(d)}
    routes=defaultdict(list)
    for r in rows:
        key=tuple(sorted((r['ORIGIN_AIRPORT_ID'],r['DEST_AIRPORT_ID'])))
        routes[key].append(float(r['DISTANCE']))
    result['route_mean']=sum(sum(v)/len(v) for v in routes.values())/len(routes)
    for field in ['SEATS','PASSENGERS','DEPARTURES_PERFORMED']:
        weights=[float(r[field]) for r in rows]
        if any(w<0 for w in weights):raise ValueError('Negative weight')
        result[field.lower()+'_weighted']=sum(x*w for x,w in zip(d,weights))/sum(weights) if sum(weights)>0 else None
    return result

def other_seats(values,country):
    """Sum all OTHER countries only when every required value is available."""
    if country not in values:raise ValueError('Unknown country')
    others=[v for c,v in values.items() if c!=country]
    if not others:raise ValueError('No comparison countries')
    return (sum(others) if all(v is not None for v in others) else None,sum(v is None for v in others))

def save(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def run(out):
    out.mkdir(parents=True,exist_ok=False)
    countries={r['bts_code']:r['reference_name'] for r in json.loads((ROOT/'config/africa-census-countries.json').read_text())['countries']}
    collpath=ROOT/'runs/bts-bulk/collection-20261118T144145700171Z.json';collection=json.loads(collpath.read_text());groups=defaultdict(list);sources=[]
    for e in collection['years']:
        p=Path(e['folder'])/'response.bin';raw=p.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=e['sha256']:raise ValueError('Source hash mismatch')
        sources.append({'path':str(p.relative_to(ROOT)),'sha256':e['sha256']})
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            with z.open(z.namelist()[0]) as stream:
                for r in csv.DictReader(io.TextIOWrapper(stream,encoding='utf-8-sig')):
                    y,m=int(r['YEAR']),int(r['MONTH'])
                    if y!=e['year'] or not 1<=m<=12:raise ValueError('Invalid source period')
                    if y==2026 and m>6:continue
                    o,d=r['ORIGIN_COUNTRY'],r['DEST_COUNTRY'];c=d if o=='US' else o if d=='US' else None
                    if c in countries:groups[c,y,(m-1)//3+1].append(r)
    ref=ROOT/'runs/reference-snapshots'/REFERENCE_HASH/'sample2.xls';raw=ref.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=REFERENCE_HASH:raise ValueError('Reference hash mismatch')
    b=xlrd.open_workbook(file_contents=raw);s=b.sheet_by_index(0);h=s.row_values(0);references=[];inverse={v:k for k,v in countries.items()}
    for n in range(1,s.nrows):
        r=dict(zip(h,s.row_values(n)));dt=xlrd.xldate_as_datetime(r['yr_qrt'],b.datemode)
        references.append((inverse[r['CTYNAME']],dt.year,(dt.month-1)//3+1,r['distance']))
    comparisons=[];extensions=[];other=[];summary={}
    for service in ['scheduled_F','all_returned_classes']:
        def selected(c,y,q):
            rows=groups[c,y,q];return [r for r in rows if r['CLASS']=='F'] if service=='scheduled_F' else rows
        for c,y,q,target in references:
            rows=selected(c,y,q);calc=distance_candidates(rows)
            for method in ['row_mean','route_mean','seats_weighted','passengers_weighted','departures_performed_weighted']:
                value=calc.get(method);diff=value-target if value is not None and target!='' else None
                comparisons.append({'service_view':service,'country':countries[c],'year':y,'quarter':q,'method':method,'source_rows':len(rows),'reference_miles':target,'candidate_miles':value,'difference_miles':diff,'within_0_001_mile':None if diff is None else abs(diff)<=.001})
        for c in countries:
            for y in range(2020,2027):
                for q in range(1,3 if y==2026 else 5):
                    rows=selected(c,y,q);calc=distance_candidates(rows)
                    extensions.append({'service_view':service,'country':countries[c],'year':y,'quarter':q,'source_rows':len(rows),'status':'DIAGNOSTIC_NOT_APPROVED' if rows else 'NO_SOURCE_ROWS',**{k:calc.get(k) for k in ['row_mean','route_mean','seats_weighted','passengers_weighted','departures_performed_weighted']}})
        # Use existing three-month-screened provisional seats, not raw partial sums.
        panelpath=ROOT/'runs/bts-panel14-20261119T145226651216Z'/service/'extension-preview.csv'
        sources.append({'path':str(panelpath.relative_to(ROOT)),'sha256':hashlib.sha256(panelpath.read_bytes()).hexdigest()})
        panel=list(csv.DictReader(panelpath.open()));periods=defaultdict(dict)
        for r in panel:
            key=(r['year'],r['quarter']);c=r['country_name']
            if c in periods[key]:raise ValueError('Duplicate panel key')
            periods[key][c]=float(r['provisional_SEATS']) if r['provisional_SEATS']!='' else None
        for (y,q),values in periods.items():
            if set(values)!=set(countries.values()):raise ValueError('Incomplete country grid')
            for c in values:
                v,n=other_seats(values,c)
                other.append({'service_view':service,'country':c,'year':y,'quarter':q,'seats_others_candidate':v,'missing_other_countries':n,'status':'PROVISIONAL_COMPLETE_OTHER_COUNTRIES' if v is not None else 'UNRESOLVED_MISSING_OTHER_COUNTRIES'})
        summary[service]={}
        for method in ['row_mean','route_mean','seats_weighted','passengers_weighted','departures_performed_weighted']:
            rs=[r for r in comparisons if r['service_view']==service and r['method']==method]
            summary[service][method]={'comparable':sum(r['difference_miles'] is not None for r in rs),'within_0_001_mile':sum(r['within_0_001_mile'] is True for r in rs)}
        summary[service]['seats_others_status']=dict(Counter(r['status'] for r in other if r['service_view']==service))
    save(out/'distance-historical-comparison.csv',comparisons);save(out/'distance-extension-diagnostics.csv',extensions);save(out/'seats-others-candidates.csv',other)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'manifest.json').write_text(json.dumps({'reference_sha256':REFERENCE_HASH,'inputs':sources,'distance_match_tolerance_miles':.001,'distance_method_selected':None,'imputation':'NONE','network_calls':0,'prior_workbooks_modified':False},indent=2)+'\n')
    print(json.dumps(summary,indent=2))
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);run(p.parse_args().output)
