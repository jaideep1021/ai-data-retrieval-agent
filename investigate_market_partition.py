"""Fit historical reference partitions as diagnostics, not carrier nationality.

Enumerates carrier subsets matching both source-row count and seats. This uses
reference answers and is NOT independent validation or an approved extension.
No existing raw source or workbook is modified. Use a fresh output directory.
"""
import csv,io,json,zipfile,hashlib,itertools
from pathlib import Path
from collections import defaultdict,Counter
import xlrd
from market_partitions import matching_partitions
import argparse
p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);args=p.parse_args()
root=Path(__file__).resolve().parent;refs={};p=root/'runs/reference-snapshots/3a37c8ed266d0687398625b49c27defeac8ff2808f63c95bf0824dcf261d1a9c/sample2.xls';b=xlrd.open_workbook(p);s=b.sheet_by_index(0);h=s.row_values(0)
for i in range(1,s.nrows):
 r=dict(zip(h,s.row_values(i)));dt=xlrd.xldate_as_datetime(r['yr_qrt'],b.datemode);refs[r['CTYNAME'],dt.year,(dt.month-1)//3+1]=r
countries={r['bts_code']:r['reference_name'] for r in json.loads((root/'config/africa-census-countries.json').read_text())['countries']};g=defaultdict(list)
for e in json.loads((root/'runs/bts-bulk/collection-20261118T144145700171Z.json').read_text())['years']:
 if e['year']>2019:continue
 raw=(Path(e['folder'])/'response.bin').read_bytes();assert hashlib.sha256(raw).hexdigest()==e['sha256']
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  with z.open(z.namelist()[0]) as f:
   for r in csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')):
    o,d=r['ORIGIN_COUNTRY'],r['DEST_COUNTRY'];c=d if o=='US' else o if d=='US' else None
    if c in countries:g[countries[c],int(r['YEAR']),(int(r['MONTH'])-1)//3+1].append(r)
counts=Counter();assigned=defaultdict(set);samples=[];allsolutions=[]
for key,ref in refs.items():
 rows=g[key]
 if not rows:counts['no_source_rows']+=1;continue
 counts['comparable']+=1;counts['counts_sum_equals_rows']+=ref['African_Market_No']+ref['International_Market_No']==len(rows)
 carriers=defaultdict(lambda:[0,0,set()])
 for r in rows:
  a=carriers[r['AIRLINE_ID']];a[0]+=1;a[1]+=int(float(r['SEATS']));a[2].add(r['UNIQUE_CARRIER'])
 ids=sorted(carriers);assert len(ids)<20
 solutions=matching_partitions(carriers,ref['African_Market_No'],ref['African_Market_Seats'])
 counts['unique_partition' if len(solutions)==1 else 'no_partition' if not solutions else 'multiple_partitions']+=1
 if len(solutions)==1:
  for c,v in solutions[0].items():assigned[c].add(v)
 allsolutions.append({'country':key[0],'year':key[1],'quarter':key[2],'solutions':solutions,'carriers':{c:[v[0],v[1],sorted(v[2])] for c,v in carriers.items()}})
print(dict(counts));print('assignments',dict((c,sorted(v)) for c,v in assigned.items()));print('conflicting carrier ids',[c for c,v in assigned.items() if len(v)>1])
out=args.output;out.mkdir(parents=True,exist_ok=False);(out/'partition-diagnostics.json').write_text(json.dumps(allsolutions,indent=2));(out/'summary.json').write_text(json.dumps(dict(counts),indent=2))
