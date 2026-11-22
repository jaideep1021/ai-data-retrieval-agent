"""Offline integrity and consolidation checks; no source refresh or model calls."""
from pathlib import Path
import csv,json,hashlib,subprocess,tempfile,sys
from openpyxl import load_workbook
root=Path(__file__).resolve().parents[1];base=root/'runs/unimputed-baseline-20261120-r3'
def read(p):
 with p.open() as f:return list(csv.DictReader(f))
for r in json.loads((base/'source-register.json').read_text()):
 assert hashlib.sha256((root/r['path']).read_bytes()).hexdigest()==r['sha256'],r['path']
with tempfile.TemporaryDirectory() as tmp:
 out=Path(tmp)/'rebuilt'
 code=(base/'consolidation-reproduction.py').read_text().replace("out=root/'runs/unimputed-baseline-20261120-r3'",'out=Path('+repr(str(out))+')')
 subprocess.run([sys.executable,'-c',code],cwd=root,check=True)
 for name in ['scheduled_F-unimputed.csv','all_returned_classes-unimputed.csv','missing-values.csv','workbook-data.json']:
  assert (out/name).read_bytes()==(base/name).read_bytes(),name
book=load_workbook(base/'outputs/review/Africa-unimputed-working-baseline.xlsx',read_only=True,data_only=True)
data=json.loads((base/'workbook-data.json').read_text())['sheets']
for item in data:
 rows=list(book[item['name']].values);headers=list(item['rows'][0]);assert list(rows[0])==headers
 assert len(rows)-1==len(item['rows'])
 for actual,expected in zip(rows[1:],item['rows']):
  for a,k in zip(actual,headers):
   e=expected[k]
   assert a==e or (isinstance(a,(int,float)) and isinstance(e,(int,float)) and abs(a-e)<=1e-9*max(1,abs(e))),(item['name'],k,a,e)
for service in ['scheduled_F','all_returned_classes']:
 rows=read(base/(service+'-unimputed.csv'));keys=[(r['country_name'],r['year'],r['quarter']) for r in rows]
 assert len(rows)==len(set(keys))==364
 assert len({k[0] for k in keys})==14
 assert all(2020<=int(y)<=2026 and 1<=int(q)<=4 and (int(y)<2026 or int(q)<=2) for _,y,q in keys)
 assert all(len(r)==57 for r in rows)
print('PASS: 199 hashes; deterministic consolidation from preserved processed inputs; 728 unique panel rows; all Excel data and missing-label rows match preserved JSON.')
