"""Preserve UN Tourism visitor definitions and compare without filling gaps.

A source estimate is retained with its flag, never labelled agent imputation.
No country-specific visitor definition is automatically chosen for extension.
"""
import csv,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
from openpyxl import load_workbook
import xlrd
from worldbank_panel import ROOT
from validate_worldbank_panel import REFERENCE_HASH,save
URL='https://pre-webunwto.s3.eu-west-1.amazonaws.com/s3fs-public/2026-09/UN_Tourism_inbound_arrivals_09_2026.xlsx'
ALIASES={'Cape Verde':'Cabo Verde',"Cote d'Ivoire":'Côte d’Ivoire'}
TYPES={'TOUR':'overnight_tourists','VSTR':'all_visitors','EXCR':'same_day_visitors'}

def convert(value,unit):
    if value is None:return None
    if unit!='thousand trips' or isinstance(value,bool) or not isinstance(value,(int,float)) or value<0:
        raise ValueError('Unexpected tourism value or unit')
    return value*1000

def run(folder):
    path=folder/'UN-Tourism-arrivals.xlsx';before=hashlib.sha256(path.read_bytes()).hexdigest()
    manifest={'source_url':URL,'sha256':before,'bytes':path.stat().st_size,
              'downloaded_utc_from_file_mtime':datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat()}
    countries=[r['reference_name'] for r in json.loads((ROOT/'config/africa-census-countries.json').read_text())['countries']]
    mapping={ALIASES.get(c,c):c for c in countries}
    book=load_workbook(path,read_only=True,data_only=True);it=book['Data'].values;header=next(it)
    needed={'indicator_code','reporter_area_label','partner_area_label','year','value','unit','flag','flag_label','notes'}
    if not needed<=set(header):raise ValueError('Source schema changed')
    selected=[];lookup={}
    for vals in it:
        r=dict(zip(header,vals));country=mapping.get(r['reporter_area_label'])
        if country is None or not 2015<=r['year']<=2026:continue
        if r['partner_area_label']!='World':raise ValueError('Unexpected partner scope')
        r['country']=country;r['value_trips']=convert(r['value'],r['unit'])
        key=(country,r['year'],r['indicator_code'])
        if key in lookup:raise ValueError('Duplicate tourism observation')
        lookup[key]=r;selected.append(r)
    save(folder/'selected-source-observations.csv',selected)
    # Explicit candidate grid; no inferred category, interpolation or carry-forward.
    grid=[]
    for country in countries:
        for year in range(2015,2027):
            for suffix,kind in TYPES.items():
                code='INBD_TRIP_TOTL_TOTL_'+suffix;r=lookup.get((country,year,code))
                grid.append({'country':country,'year':year,'visitor_type':kind,'indicator':code,
                             'trips':None if r is None else r['value_trips'],
                             'status':'NOT_REPORTED_IN_DOWNLOADED_FILE' if r is None else 'SOURCE_VALUE' if r['value'] is not None else 'SOURCE_MISSING',
                             'source_flag':None if r is None else r['flag_label'],
                             'source_notes':None if r is None else r['notes']})
    save(folder/'annual-candidates.csv',grid)
    ref=ROOT/'runs/reference-snapshots'/REFERENCE_HASH/'sample2.xls'
    assert hashlib.sha256(ref.read_bytes()).hexdigest()==REFERENCE_HASH
    rb=xlrd.open_workbook(ref);sheet=rb.sheet_by_index(0);h=sheet.row_values(0);refs={}
    for n in range(1,sheet.nrows):
        vals=sheet.row_values(n);y=xlrd.xldate_as_datetime(vals[1],rb.datemode).year;k=(vals[0],y);v=vals[h.index('Tourism_T')]
        if k in refs and refs[k]!=v:raise ValueError('Within-year variation')
        refs[k]=v
    comparison=[];bycountry={}
    for country in countries:
        bycountry[country]={}
        for suffix,kind in TYPES.items():
            pairs=matches=0
            for year in range(2015,2020):
                refval=refs[country,year];r=lookup.get((country,year,'INBD_TRIP_TOTL_TOTL_'+suffix));v=None if r is None else r['value_trips']
                difference=None if v is None or refval=='' else v-refval
                if difference is not None:pairs+=1;matches+=abs(difference)<=1
                comparison.append({'country':country,'year':year,'visitor_type':kind,'reference':refval,'source_trips':v,'difference':difference})
            bycountry[country][kind]={'comparable_years':pairs,'within_one_trip':matches}
    save(folder/'reference-arrivals-comparison.csv',comparison)
    summary={'selected_source_rows':len(selected),'annual_candidate_grid_rows':len(grid),
             'availability':{kind:{str(y):sum(r['visitor_type']==kind and r['year']==y and r['trips'] is not None for r in grid) for y in range(2020,2027)} for kind in TYPES.values()},
             'historical_comparison':bycountry,
             'source_warning':'New unified collection system is transitional; preserve definitions, flags and source notes.',
             'extension_mapping':'NO_AUTOMATIC_VISITOR_CATEGORY_SELECTION'}
    (folder/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (folder/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    assert hashlib.sha256(path.read_bytes()).hexdigest()==before
    assert hashlib.sha256(ref.read_bytes()).hexdigest()==REFERENCE_HASH
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);run(p.parse_args().folder)
