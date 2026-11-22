"""Preserve dated World Bank income groups as an alternative to fixed labels.

World Bank fiscal years begin July 1 of the previous calendar year. The income
measurement year is not the classification's effective year. No latest label is
backfilled into earlier quarters, and the reference is never overwritten.
"""
import io,csv,json,hashlib,re
from pathlib import Path
from collections import defaultdict
from openpyxl import load_workbook
import xlrd
from worldbank_panel import ROOT
from validate_worldbank_panel import REFERENCE_HASH
NAMES={'Cape Verde':'Cabo Verde','Egypt':'Egypt, Arab Rep.',"Cote d'Ivoire":"Côte d'Ivoire"}
LABELS={'L':'Low income','LM':'Lower middle income','UM':'Upper middle income','H':'High income'}
def fiscal_year(year,quarter):
    if quarter not in (1,2,3,4):raise ValueError('Invalid quarter')
    return year+(quarter>=3)
def save(path,rows):
    with path.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def run(folder):
    raw=(folder/'download.response').read_bytes();assert hashlib.sha256(raw).hexdigest()==json.loads((folder/'manifest.json').read_text())['sha256']
    book=load_workbook(io.BytesIO(raw),read_only=True,data_only=True);s=book['Country Analytical History'];rows=list(s.values)
    cols={2000+int(v[2:]) if int(v[2:])<80 else 1900+int(v[2:]):i for i,v in enumerate(rows[4]) if isinstance(v,str) and re.fullmatch(r'FY\d{2}',v)}
    countries=[r['reference_name'] for r in json.loads((ROOT/'config/africa-census-countries.json').read_text())['countries']]
    byname={r[1]:r for r in rows[6:] if r[0] and r[1]};lookup={};annual=[]
    for c in countries:
        r=byname[NAMES.get(c,c)]
        for fy,i in sorted(cols.items()):
            code=r[i];label=LABELS.get(code)
            if code not in LABELS and code not in (None,'','..','Unclassified'):raise ValueError(f'Unknown source code: {code}')
            lookup[c,fy]=label;annual.append({'country':c,'fiscal_year':fy,'effective_from':f'{fy-1}-07-01','effective_to':f'{fy}-06-30','gni_measurement_year':rows[5][i],'income_group':label,'source_code':code})
    save(folder/'annual-classifications.csv',annual)
    ref=ROOT/'runs/reference-snapshots'/REFERENCE_HASH/'sample2.xls';assert hashlib.sha256(ref.read_bytes()).hexdigest()==REFERENCE_HASH
    b=xlrd.open_workbook(ref);sheet=b.sheet_by_index(0);h=sheet.row_values(0);fixed=defaultdict(set);comparison=[]
    for i in range(1,sheet.nrows):
        r=dict(zip(h,sheet.row_values(i)));dt=xlrd.xldate_as_datetime(r['yr_qrt'],b.datemode);q=(dt.month-1)//3+1;fy=fiscal_year(dt.year,q);c=r['CTYNAME'];fixed[c].add(r['IncomeGroup']);value=lookup.get((c,fy))
        comparison.append({'country':c,'year':dt.year,'quarter':q,'reference':r['IncomeGroup'],'effective_fiscal_year':fy,'source_group':value,'match':value==r['IncomeGroup']})
    assert all(len(v)==1 for v in fixed.values())
    matching=[fy for fy in cols if all(lookup.get((c,fy))==next(iter(fixed[c])) for c in countries)]
    extension=[]
    for c in countries:
        for y in range(2020,2027):
            for q in range(1,3 if y==2026 else 5):
                fy=fiscal_year(y,q);v=lookup.get((c,fy));extension.append({'country':c,'year':y,'quarter':q,'IncomeGroup_effective_FY_candidate':v,'IncomeGroup_source_FY':fy,'status':'DATED_ALTERNATIVE_NOT_ORIGINAL_FIXED_RULE' if v else 'SOURCE_UNCLASSIFIED_OR_MISSING'})
    save(folder/'historical-comparison.csv',comparison);save(folder/'quarterly-candidates.csv',extension)
    summary={'reference_fixed_within_each_country':True,'reference_quarters':280,'matches_effective_quarter_classification':sum(r['match'] for r in comparison),'whole_sample_matching_fixed_fiscal_years':sorted(matching),'extension_rows':len(extension),'extension_nonmissing':sum(r['IncomeGroup_effective_FY_candidate'] is not None for r in extension),'source_fiscal_year_max':max(cols),'parameter_sheet_warning':'Parameters sheet says FY21; actual history headers extend to FY27. Used explicit history headers and source effective-date note.'}
    (folder/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);run(p.parse_args().folder)
