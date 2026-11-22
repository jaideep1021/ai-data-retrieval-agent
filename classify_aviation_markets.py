"""Compare reference market labels with dated BTS foreign-carrier groups.

Group zero means Foreign Carriers in the downloaded CarrierGroupNew lookup.
Do not rename that category African. Missing or temporally ambiguous mappings
remain unresolved; source-detail counts are not distinct airlines or routes.
"""
import csv,io,json,zipfile,hashlib,calendar
from collections import defaultdict,Counter
from datetime import datetime,date
from pathlib import Path
import xlrd
from worldbank_panel import ROOT
from validate_worldbank_panel import REFERENCE_HASH

def parse_date(value):
    return datetime.strptime(value.split()[0],'%m/%d/%Y').date() if value else None

def classify(row,lookup):
    """Require a classification covering the whole source month.

    Multiple dated name records may coexist; agree on group zero versus nonzero
    or abstain. Never fall back to a guessed carrier-code prefix or name.
    """
    y,m=int(row['YEAR']),int(row['MONTH']);first=date(y,m,1);last=date(y,m,calendar.monthrange(y,m)[1])
    records=lookup.get((row['AIRLINE_ID'],row['UNIQUE_CARRIER_ENTITY']),[])
    groups=set();overlapping=set()
    for r in records:
        start,end=parse_date(r['START_DATE_SOURCE']),parse_date(r['THRU_DATE_SOURCE'])
        g=r['CARRIER_GROUP_NEW']
        if start is None or g not in {'0','1','2','3','4','5','6','7','9'}:
            return None
        if start<=last and (end is None or end>=first):overlapping.add(g=='0')
        if start<=first and (end is None or end>=last):groups.add(g=='0')
    return next(iter(groups)) if len(groups)==1 and len(overlapping)==1 else None

def write(p,rows):
    with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def run(folder):
    raw=(folder/'response.bin').read_bytes();meta=json.loads((folder/'manifest.json').read_text())
    assert hashlib.sha256(raw).hexdigest()==meta['sha256']
    with zipfile.ZipFile(io.BytesIO(raw)) as z:carriers=list(csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]),encoding='utf-8-sig')))
    lookup=defaultdict(list)
    for r in carriers:lookup[r['AIRLINE_ID'],r['UNIQUE_CARRIER_ENTITY']].append(r)
    dictionary=list(csv.DictReader((folder/'carrier-group-new.csv').open()))
    assert any(r['Code']=='0' and r['Description']=='Foreign Carriers' for r in dictionary)
    countries={r['bts_code']:r['reference_name'] for r in json.loads((ROOT/'config/africa-census-countries.json').read_text())['countries']}
    groups=defaultdict(list);unmapped=Counter();source_manifest=[]
    for e in json.loads((ROOT/'runs/bts-bulk/collection-20261118T144145700171Z.json').read_text())['years']:
        p=Path(e['folder'])/'response.bin';raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==e['sha256'];source_manifest.append({'path':str(p),'sha256':e['sha256']})
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for r in csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]),encoding='utf-8-sig')):
                y,m=int(r['YEAR']),int(r['MONTH'])
                if y==2026 and m>6:continue
                o,d=r['ORIGIN_COUNTRY'],r['DEST_COUNTRY'];c=d if o=='US' else o if d=='US' else None
                if c not in countries:continue
                r['foreign']=classify(r,lookup);groups[countries[c],y,(m-1)//3+1].append(r)
                if r['foreign'] is None:unmapped[r['AIRLINE_ID'],r['UNIQUE_CARRIER_ENTITY'],y]+=1
    ref=ROOT/'runs/reference-snapshots'/REFERENCE_HASH/'sample2.xls';assert hashlib.sha256(ref.read_bytes()).hexdigest()==REFERENCE_HASH
    b=xlrd.open_workbook(ref);s=b.sheet_by_index(0);h=s.row_values(0);comp=[]
    def aggregate(rows):
        if not rows or any(r['foreign'] is None for r in rows):return [None]*4
        return [sum(r['foreign'] for r in rows),sum(not r['foreign'] for r in rows),sum(float(r['SEATS']) for r in rows if r['foreign']),sum(float(r['SEATS']) for r in rows if not r['foreign'])]
    fields=['African_Market_No','International_Market_No','African_Market_Seats','International_Market_Seats']
    for i in range(1,s.nrows):
        r=dict(zip(h,s.row_values(i)));dt=xlrd.xldate_as_datetime(r['yr_qrt'],b.datemode);q=(dt.month-1)//3+1;rows=groups[r['CTYNAME'],dt.year,q];vals=aggregate(rows)
        for f,v in zip(fields,vals):comp.append({'country':r['CTYNAME'],'year':dt.year,'quarter':q,'reference_field':f,'reference':r[f],'source_candidate':v,'exact_match':v==r[f] if v is not None and r[f]!='' else None,'source_rows':len(rows)})
    extension=[]
    for service in ['scheduled_F','all_returned_classes']:
        p=ROOT/'runs/bts-panel14-20261119T145226651216Z'/service/'extension-preview.csv'
        for r in csv.DictReader(p.open()):
            c,y,q=r['country_name'],int(r['year']),int(r['quarter']);rows=groups[c,y,q];rows=[v for v in rows if v['CLASS']=='F'] if service=='scheduled_F' else rows;vals=aggregate(rows);complete=r['provisional_SEATS']!=''
            out={'service_view':service,'country':c,'year':y,'quarter':q,'source_rows':len(rows),'unclassified_rows':sum(v['foreign'] is None for v in rows),'coverage_status':r['status'],'definition_status':'FOREIGN_VS_NONFOREIGN_NOT_AFRICAN_NATIONALITY'}
            for k,v in zip(['foreign_record_count','nonforeign_record_count','foreign_seats','nonforeign_seats'],vals):out['observed_'+k]=v;out['provisional_'+k]=v if complete else None
            extension.append(out)
    write(folder/'historical-classification-comparison.csv',comp);write(folder/'market-extension-candidates.csv',extension)
    summary={'lookup_rows':len(carriers),'historical':{f:{'comparable':sum(r['reference_field']==f and r['exact_match'] is not None for r in comp),'exact_matches':sum(r['reference_field']==f and r['exact_match'] is True for r in comp)} for f in fields},'unclassified_source_rows':sum(unmapped.values()),'extension':{service:{'rows':364,'classified_observed':sum(r['service_view']==service and r['observed_foreign_record_count'] is not None for r in extension),'provisional_three_month_screen':sum(r['service_view']==service and r['provisional_foreign_record_count'] is not None for r in extension)} for service in ['scheduled_F','all_returned_classes']}}
    (folder/'classification-summary.json').write_text(json.dumps(summary,indent=2)+'\n');(folder/'input-hashes.json').write_text(json.dumps(source_manifest,indent=2));(folder/'unclassified-records.json').write_text(json.dumps([{'airline_id':k[0],'entity':k[1],'year':k[2],'rows':v} for k,v in unmapped.items()],indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);run(p.parse_args().folder)
