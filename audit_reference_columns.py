"""Inventory all reference fields and document completion without altering data.

Status is a research judgment, kept separate from automatically measured counts.
Numerical identities are diagnostic evidence, not proof of author intent.
"""
import csv,json,hashlib
from collections import Counter,defaultdict
from pathlib import Path
import xlrd
from worldbank_panel import ROOT
from validate_worldbank_panel import REFERENCE_HASH
# Each original field must appear exactly once; never silently drop an unknown.
SPEC={
'CTYNAME':('IMPLEMENTED','country_name / country_code','14-country mapping established','None'),
'yr_qrt':('IMPLEMENTED','year / quarter','364 extension keys per service view','None'),
'seats':('PROVISIONAL','observed_SEATS / provisional_SEATS','183 historical positives reproduce under all classes; 97 reference zeros have no source rows','Confirm service scope and absent-record treatment'),
'passengers':('PROVISIONAL','observed_PASSENGERS / provisional_PASSENGERS','Same historical reproduction as seats','Confirm service scope and absent-record treatment'),
'distance':('NOT_EXTENDED','None','Raw BTS miles exist; aggregation not established','Test row, route and weighted means; investigate reference values without bilateral rows'),
'African_Market_No':('NOT_EXTENDED','None','Meaning of African market not established','Identify carrier/route classification and counting rule'),
'International_Market_No':('NOT_EXTENDED','None','Meaning of international market not established','Identify carrier/route classification and counting rule'),
'African_Market_Seats':('NOT_EXTENDED','None','Paired seat columns sum to total in 183 comparable rows','Identify classification before assigning seats'),
'International_Market_Seats':('NOT_EXTENDED','None','Paired seat columns sum to total in 183 comparable rows','Identify classification before assigning seats'),
'CountAirline':('PROVISIONAL','DistinctAirlineCount / SourceRecordCount','Supervisor approved retaining both measures; reference product kept separately','Retain both; do not rename either as a proved original CountAirline definition'),
'AC':('NOT_OBTAINED','AC remains blank','Public ranks and growth are not compatible index levels','Obtain original index specification and compatible data access'),
'GDP_T':('PROVISIONAL','GDP_current_USD_candidate','Historical comparisons differ; current USD candidate collected','Resolve vintage/definition differences'),
'Population_T':('PROVISIONAL','Population_persons_candidate','Annual population candidate collected; historical revisions not proved','Resolve vintage/definition differences'),
'Costpergallon':('PROVISIONAL','EIA and BTS fuel candidates','240/280 reference values match BTS quarter-end within half a cent','Resolve remaining 40 and country-specific month rule'),
'Fuel_Cost_Africa':('PROVISIONAL','Blank; country-factor diagnostic only','Country-specific factors inferred but meaning unknown','Confirm factor definition; do not extrapolate inferred factors'),
'Tourism_Y':('PROVISIONAL','Tourism_expenditure_pct_imports_candidate','61/63 historical comparisons within 0.1%; 11 countries available in 2020','Keep later gaps; seek newer compatible source if required'),
'Tourism_T':('PROVISIONAL','Tourism_arrivals_trips_candidate','61 nonmissing historical annual values match country-specific visitor categories','Keep inferred category and source flags explicit'),
'Tourism_P':('PROVISIONAL','Tourism_receipts_pct_exports_candidate','67/69 historical comparisons within 0.1%; 11 countries available in 2020','Keep later gaps; seek newer compatible source if required'),
'IYR':('IMPLEMENTED','Separate Census annual table','Annual imports in USD millions; full 2026 annual value blank','Reference date issue deferred; do not imply exact historical replication'),
'EYR':('IMPLEMENTED','Separate Census annual table','Annual exports in USD millions; full 2026 annual value blank','Reference date issue deferred; do not imply exact historical replication'),
'IQ':('IMPLEMENTED','imports_usd_millions','Complete monthly sums through 2026 Q2','Reference date issue deferred'),
'EQ':('IMPLEMENTED','exports_usd_millions','Complete monthly sums through 2026 Q2','Reference date issue deferred'),
'ExportHi':('EXCLUDED_BY_USER','Not extended','Explicit user instruction to ignore','None'),
'ImportHi':('EXCLUDED_BY_USER','Not extended','Explicit user instruction to ignore','None'),
'Exchange':('PROVISIONAL','Exchange_LCU_per_USD_candidate','65/65 available historical comparisons within 0.1%','Maintain source gaps; confirm final mapping'),
'PPP':('PROVISIONAL','PPP_LCU_per_international_dollar_candidate','Conversion-factor candidate; historical differences remain','Confirm PPP definition and vintage'),
'IncomeGroup':('NOT_EXTENDED','None','Historical classification not yet mapped','Establish fixed versus time-varying classification and source year'),
'Immigration':('PROVISIONAL','ACS_foreign_born_persons_alternative','Alternative has margins of error; original units/year unknown','Confirm original measure or approve alternative explicitly'),
'seats_others':('NOT_EXTENDED','None','280/280 reference rows equal sum across 14 countries minus own seats','Implement candidate only with explicit missing-country handling')}

def run(out):
 out.mkdir(parents=True,exist_ok=False)
 ref=ROOT/'runs/reference-snapshots'/REFERENCE_HASH/'sample2.xls';raw=ref.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=REFERENCE_HASH:raise ValueError('Reference hash changed')
 book=xlrd.open_workbook(file_contents=raw);s=book.sheet_by_index(0);headers=s.row_values(0)
 if len(headers)!=29 or set(headers)!=set(SPEC):raise ValueError('Unmapped reference field')
 rows=[dict(zip(headers,s.row_values(i))) for i in range(1,s.nrows)]
 totals=defaultdict(float)
 for r in rows:totals[r['yr_qrt']]+=r['seats']
 identities=[]
 for r in rows:
  d=xlrd.xldate_as_datetime(r['yr_qrt'],book.datemode)
  identities.append({'country':r['CTYNAME'],'year':d.year,'quarter':(d.month-1)//3+1,'reference_seats_others':r['seats_others'],'sum_14_minus_own':totals[r['yr_qrt']]-r['seats'],'matches':r['seats_others']==totals[r['yr_qrt']]-r['seats']})
 audit=[]
 for f in headers:
  status,output,evidence,nextstep=SPEC[f]
  audit.append({'reference_field':f,'status':status,'reference_nonmissing_rows':sum(r[f]!='' for r in rows),'current_output':output,'evidence':evidence,'next_action':nextstep})
 for name,data in [('column-audit.csv',audit),('seats-others-identity.csv',identities)]:
  with (out/name).open('w',newline='') as stream:w=csv.DictWriter(stream,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
 counts=dict(Counter(r['status'] for r in audit));summary={'reference_sha256':REFERENCE_HASH,'reference_rows':len(rows),'reference_columns':len(headers),'status_counts':counts,'seats_others_identity_matches':sum(r['matches'] for r in identities),'no_data_changed':True,'network_calls':0}
 (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 text='# Reference column completion audit\n\nAll 29 columns in the supplied 2015–2019 reference are accounted for. Status counts measure fields, not effort or overall project completion. IMPLEMENTED means the source processing exists; it does not establish exact replication of all historical values.\n\n'
 text+='| Status | Fields |\n|---|---:|\n'+''.join(f'| {k} | {v} |\n' for k,v in counts.items())
 text+='\n| Reference field | Status | Current output | Next action |\n|---|---|---|---|\n'+''.join(f"| {r['reference_field']} | {r['status']} | {r['current_output']} | {r['next_action']} |\n" for r in audit)
 text+='\n## Next implementation checkpoint\n\nTest distance aggregation and the seats_others identity against preserved BTS data. The market split requires a classification rule; its labels are not sufficient evidence. A sum involving a missing country must not silently treat that country as zero. Keep these diagnostics separate from the preserved workbook until reviewed.\n\nThe full historical workbook is not a prerequisite for delivering the extension: supply the unchanged 2015–2019 reference alongside a separate extension. Do not claim that unavailable 2009–2014 history was appended. BLS employment/unemployment and an explicit Nonstop indicator were mentioned in the assignment but are absent from the 29-column reference; their exact definitions and inclusion need resolution rather than assumed mappings. Flight frequency and freight have BTS candidate outputs already.\n'
 (out/'column-audit.md').write_text(text)
 assert hashlib.sha256(ref.read_bytes()).hexdigest()==REFERENCE_HASH
 print(json.dumps(summary,indent=2))
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);run(p.parse_args().output)
