"""Compare annual candidates with the private reference and repeat by quarter.

Outputs remain candidates: numerical similarity does not prove series identity.
No old data are overwritten, and annual GDP is never divided by four.
"""
import csv
import hashlib
import json
import statistics
from pathlib import Path
import xlrd
from worldbank_panel import ROOT

MAPPING = {'GDP_T':'NY.GDP.MKTP.CD', 'Population_T':'SP.POP.TOTL',
           'PPP':'PA.NUS.PPP', 'Exchange':'PA.NUS.FCRF'}
REFERENCE_HASH = '3a37c8ed266d0687398625b49c27defeac8ff2808f63c95bf0824dcf261d1a9c'

def expand(annual, countries):
    """Repeat same-year annual values; preserve missing values and June cutoff."""
    lookup = {}
    for r in annual:
        key = (r['country'], int(r['year']), r['indicator'])
        if key in lookup: raise ValueError('Duplicate annual key')
        lookup[key] = r['value']
    result = []
    for country in countries:
        for year in range(2020, 2027):
            for quarter in range(1, 3 if year == 2026 else 5):
                row = {'country':country, 'year':year, 'quarter':quarter}
                for name, code in MAPPING.items():
                    row[name] = lookup.get((country,year,code))
                result.append(row)
    return result

def save(path, rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def run(folder):
    # Verify original bytes and downloaded responses before using either.
    ref=ROOT/'runs/reference-snapshots'/REFERENCE_HASH/'sample2.xls'
    before=hashlib.sha256(ref.read_bytes()).hexdigest()
    if before != REFERENCE_HASH: raise ValueError('Reference changed')
    for filename,m in json.loads((folder/'manifest.json').read_text()).items():
        if hashlib.sha256((folder/filename).read_bytes()).hexdigest()!=m['sha256']:
            raise ValueError('Source bytes changed')
    annual=list(csv.DictReader((folder/'annual-candidates.csv').open()))
    lookup={(r['country'],int(r['year']),r['indicator']):r['value'] for r in annual}
    if len(lookup)!=len(annual):raise ValueError('Duplicate source key')
    book=xlrd.open_workbook(ref);sheet=book.sheet_by_index(0);header=sheet.row_values(0)
    groups={}
    for i in range(1,sheet.nrows):
        vals=sheet.row_values(i);dt=xlrd.xldate_as_datetime(vals[1],book.datemode)
        key=(vals[0],dt.year);q=(dt.month-1)//3+1
        if q in groups.setdefault(key,{}):raise ValueError('Duplicate reference quarter')
        groups[key][q]={field:vals[header.index(field)] for field in MAPPING}
    comparisons=[];summary={}
    for field,code in MAPPING.items():
        differences=[];ratios=[]
        for (country,year),quarters in groups.items():
            if set(quarters)!={1,2,3,4}:raise ValueError('Incomplete reference year')
            values={q[field] for q in quarters.values()}
            if len(values)!=1:raise ValueError('Reference varies within year')
            original=values.pop();raw=lookup[(country,year,code)]
            value=float(raw) if raw!='' else None
            relative=abs(value-original)/abs(original) if value is not None and original!=0 else None
            comparisons.append({'country':country,'year':year,'field':field,'indicator':code,
                                'reference':original,'current_worldbank':value,
                                'difference':None if value is None else value-original,
                                'absolute_relative_difference':relative})
            if relative is not None:differences.append(relative);ratios.append(value/original)
        summary[field]={'reference_country_years':len(groups),'comparable':len(differences),
                        'within_0_1_percent':sum(x<=.001 for x in differences),
                        'within_5_percent':sum(x<=.05 for x in differences),
                        'median_current_to_reference_ratio':statistics.median(ratios)}
    countries=[r['reference_name'] for r in json.loads((ROOT/'config/africa-census-countries.json').read_text())['countries']]
    quarterly=expand(annual,countries)
    assert len(quarterly)==364
    summary['extension_missing_cells']={f:sum(r[f] in (None,'') for r in quarterly) for f in MAPPING}
    summary['quarterly_rows']=len(quarterly)
    summary['status']='CANDIDATE_MAPPING_REVIEW_REQUIRED'
    save(folder/'historical-mapping-comparison.csv',comparisons)
    save(folder/'quarterly-extension-candidates.csv',quarterly)
    assert hashlib.sha256(ref.read_bytes()).hexdigest()==before
    (folder/'mapping-validation.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path)
    run(p.parse_args().folder)
