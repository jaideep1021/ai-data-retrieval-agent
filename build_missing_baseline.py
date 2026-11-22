"""Freeze a versioned, unimputed working panel and a source-file hash register.

Two aviation service views remain separate. Candidate source values use explicit
column names and are not renamed to imply replication of unresolved variables.
Raw downloads are preserved in place; the register detects later byte changes.
"""
import csv,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
from worldbank_panel import ROOT

REMOVED={'approved_CountAirline','CountDecision','definition_status'}

def read(path):
    with path.open(newline='') as f:return list(csv.DictReader(f))

def index(rows,keys):
    result={}
    for r in rows:
        k=tuple(str(r[v]) for v in keys)
        if k in result:raise ValueError('Duplicate join key')
        result[k]=r
    return result

def write(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def run(out):
    out.mkdir(parents=True,exist_ok=False)
    census=ROOT/'runs/census-panel-20261119';wb=ROOT/'runs/worldbank-candidates-20261119'
    tourism=ROOT/'runs/tourism-recovery-20261120';imm=ROOT/'runs/immigration-candidates-20261120'
    bts=ROOT/'runs/bts-panel14-20261119T145226651216Z';fuel=ROOT/'runs/fuel-source-check-20261119'
    trade=index(read(census/'quarterly.csv'),('country','year','quarter'))
    economic=index(read(wb/'quarterly-extension-candidates.csv'),('country','year','quarter'))
    migration=index(read(imm/'annual-candidates.csv'),('country','year'))
    visits=index(read(tourism/'annual-candidates.csv'),('country','year','visitor_type'))
    prices=index(read(fuel/'quarterly-source-candidates.csv'),('year','quarter'))
    review=json.loads((tourism/'summary.json').read_text())['historical_comparison']
    mapping={}
    for country,types in review.items():
        matches=[(kind,v['comparable_years']) for kind,v in types.items() if v['comparable_years']>0 and v['within_one_trip']==v['comparable_years']]
        if len(matches)==1:mapping[country]=matches[0]
    issues=[];summary={};output_paths=[]
    for service in ['scheduled_F','all_returned_classes']:
        rows=read(bts/service/'extension-preview.csv');seen=set();panel=[]
        for r in rows:
            key=(r['country_name'],r['year'],r['quarter'])
            if key in seen:raise ValueError('Duplicate BTS key')
            seen.add(key);t=trade[key];e=economic[key];m=migration[key[:2]];f=prices[key[1:]]
            row={k:v for k,v in r.items() if k not in REMOVED}
            row.update({k:t[k] for k in ['imports_usd_millions','exports_usd_millions','total_trade_usd_millions']})
            row.update({'GDP_current_USD_candidate':e['GDP_T'],'Population_persons_candidate':e['Population_T'],
                        'PPP_LCU_per_international_dollar_candidate':e['PPP'],'Exchange_LCU_per_USD_candidate':e['Exchange'],
                        'ACS_foreign_born_persons_alternative':m['estimate_persons'],
                        'ACS_margin_of_error_persons':m['margin_of_error_persons']})
            match=mapping.get(key[0]);v=visits.get((key[0],key[1],match[0])) if match else None
            row.update({'Tourism_arrivals_trips_candidate':v['trips'] if v else '',
                        'Tourism_arrivals_basis':match[0] if match else '',
                        'Tourism_receipts_pct_exports':'','Tourism_expenditure_pct_imports':'',
                        'EIA_spot_equal_month_mean_USD_gallon_candidate':f['eia_equal_month_mean_usd_gallon'],
                        'BTS_quarter_end_USD_gallon_candidate':f['bts_quarter_end_month_usd_gallon'],
                        'Fuel_Cost_Africa':'','AC':''})
            panel.append(row)
            # A separate long log keeps status details out of numeric columns.
            for field,value in row.items():
                if value not in ('',None):continue
                if field in ('Tourism_receipts_pct_exports','Tourism_expenditure_pct_imports'):reason='SOURCE_RETRIEVAL_INCOMPLETE'
                elif field=='Fuel_Cost_Africa':reason='FORMULA_NOT_CONFIRMED'
                elif field=='AC':reason='COMPATIBLE_INDEX_LEVEL_SERIES_NOT_OBTAINED'
                elif field.startswith('ACS_'):reason=m['status']
                elif field=='Tourism_arrivals_trips_candidate':reason=v['status'] if v else 'CATEGORY_MAPPING_UNRESOLVED'
                elif field.endswith('_candidate'):reason='SOURCE_VALUE_UNAVAILABLE'
                else:reason='BTS_PRESERVED_BLANK_SEE_COVERAGE_STATUS'
                issues.append({'service_view':service,'country':key[0],'year':key[1],'quarter':key[2],'field':field,'reason':reason})
        if len(panel)!=364:raise ValueError('Incomplete extension grid')
        path=out/(service+'-unimputed.csv');write(path,panel);output_paths.append(path)
        summary[service]={'rows':len(panel),'columns':len(panel[0])}
    write(out/'missing-values.csv',issues)
    mappings=[{'country':c,'category':v[0],'matching_historical_years':v[1],'status':'INFERRED_FROM_REFERENCE_NOT_INDEPENDENTLY_APPROVED'} for c,v in mapping.items()]
    write(out/'tourism-category-evidence.csv',mappings)
    # Hash every raw/derived input in the relevant source packages, without moving
    # or overwriting original files. Do not include credentials or other runs.
    roots=[census,wb,tourism,imm,fuel,bts,ROOT/'runs/bts-bulk',ROOT/'runs/connectivity-check-20261120',ROOT/'runs/reference-snapshots/3a37c8ed266d0687398625b49c27defeac8ff2808f63c95bf0824dcf261d1a9c']
    register=[]
    for folder in roots:
        for p in sorted(folder.rglob('*')):
            if p.is_file():register.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    (out/'source-register.json').write_text(json.dumps(register,indent=2)+'\n')
    note={'created_utc':datetime.now(timezone.utc).isoformat(),'version':'unimputed-working-baseline-20261120',
          'status':'CANDIDATE_DEFINITIONS_REMAIN_UNRESOLVED','period':'2020 Q1 through 2026 Q2',
          'imputation':'NONE','source_files_preserved_in_place':True,'views':summary,
          'limitations':['Not the unavailable full 2009–2019 workbook; no historical merge claimed.',
          'Both BTS service views retained; provisional blanks and observed zeros preserved.',
          'Annual economic and tourism values repeat across quarters, not quarterly flows.',
          'ACS estimates are an alternative in persons, not a validated replacement of Immigration.',
          'Tourism categories inferred from historical matches; source notes/flags remain in source package.',
          'Fuel definitions unresolved; candidate measures do not fill Fuel_Cost_Africa.',
          'AC missing: rankings/growth rates are not index levels.',
          'Source-reported estimates are not AI-generated imputation.'],
          'outputs':[{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in output_paths]}
    (out/'manifest.json').write_text(json.dumps(note,indent=2)+'\n')
    print(json.dumps(summary));print('Source files registered',len(register));print('Missing cells logged',len(issues))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);run(p.parse_args().folder)
