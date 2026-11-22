"""Read-only 2015–2019 comparison; never change data to manufacture agreement.

Requires xlrd for legacy .xls input. Country mapping comes from a saved official
BTS lookup. Empty selections are diagnosed against reference zeros separately,
not converted to approved zeros for the extension. Alternative counts are
hypothesis diagnostics, not automatic replacements for the documented metric.
"""
import argparse
from collections import defaultdict, Counter
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import zipfile
from bts_quarterly_preview import numeric, write_csv


def compare(reference, groups):
    results=[]
    for ref in reference:
        group=groups.get((ref['code'],ref['year'],ref['quarter']),[])
        scheduled=[r for r in group if r['CLASS']=='F']
        result={k:ref[k] for k in ['country','code','year','quarter','excel_row']}
        result['F_source_rows']=len(scheduled)
        result['F_months']=','.join(map(str,sorted({int(r['MONTH']) for r in scheduled})))
        for field in ['seats','passengers']:
            target=numeric(str(ref[field]))
            observed=sum((numeric(r[field.upper()]) for r in scheduled),Decimal(0)) if scheduled else None
            result['reference_'+field]=str(target)
            result['F_'+field]=str(observed) if observed is not None else None
            result['difference_'+field]=str(observed-target) if observed is not None else None
            result['status_'+field]=('NO_F_ROWS_REFERENCE_ZERO' if target==0 else 'NO_F_ROWS_REFERENCE_NONZERO') if observed is None else 'EXACT_MATCH' if observed==target else 'DIFFERENT'
            result['all_classes_'+field]=str(sum((numeric(r[field.upper()]) for r in group),Decimal(0))) if group else None
        result['reference_CountAirline']=ref['CountAirline']
        result['F_distinct_operating_airlines']=len({r['AIRLINE_ID'] for r in scheduled if numeric(r['DEPARTURES_PERFORMED'])>0}) if scheduled else None
        result['F_distinct_reported_airlines']=len({r['AIRLINE_ID'] for r in scheduled}) if scheduled else None
        result['F_monthly_distinct_sum']=sum(len({r['AIRLINE_ID'] for r in scheduled if int(r['MONTH'])==m}) for m in range(ref['quarter']*3-2,ref['quarter']*3+1)) if scheduled else None
        result['all_classes_source_rows']=len(group)
        result['all_classes_distinct_airlines']=len({r['AIRLINE_ID'] for r in group}) if group else None
        result['diagnostic_rows_times_distinct']=len(group)*len({r['AIRLINE_ID'] for r in group}) if group else None
        result['reference_distance']=ref['distance']
        result['F_unweighted_row_mean_distance']=str(sum(numeric(r['DISTANCE']) for r in scheduled)/len(scheduled)) if scheduled else None
        results.append(result)
    return results


def run():
    import xlrd
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--collection',type=Path,required=True)
    parser.add_argument('--country-lookup',type=Path,required=True)
    args=parser.parse_args()
    raw=args.reference.read_bytes(); digest=hashlib.sha256(raw).hexdigest()
    book=xlrd.open_workbook(file_contents=raw)
    sheet=book.sheet_by_index(0); headers=sheet.row_values(0)
    required={'CTYNAME','yr_qrt','seats','passengers','distance','CountAirline'}
    if len(headers)!=len(set(headers)) or not required.issubset(headers):raise ValueError('Reference schema mismatch')
    lookup_bytes=args.country_lookup.read_bytes()
    lookup={r['Description']:r['Code'] for r in csv.DictReader(io.StringIO(lookup_bytes.decode('utf-8-sig')))}
    references=[];seen=set()
    for i in range(1,sheet.nrows):
        row=dict(zip(headers,sheet.row_values(i)))
        date=xlrd.xldate_as_datetime(row['yr_qrt'],book.datemode)
        if date.year not in range(2015,2020) or date.month not in (1,4,7,10) or date.day!=1:raise ValueError('Unexpected reference period')
        country=row['CTYNAME'];code=lookup[country];q=(date.month-1)//3+1
        key=(code,date.year,q)
        if key in seen:raise ValueError('Duplicate reference key')
        seen.add(key)
        references.append({'country':country,'code':code,'year':date.year,'quarter':q,'excel_row':i+1,
                           **{k:row[k] for k in ['seats','passengers','distance','CountAirline']}})
    if len(references)!=280 or len({r['code'] for r in references})!=14:raise ValueError('Unexpected reference coverage')
    collection_bytes=args.collection.read_bytes();collection=json.loads(collection_bytes)
    entries=[e for e in collection['years'] if 2015<=e['year']<=2019]
    if sorted(e['year'] for e in entries)!=list(range(2015,2020)):raise ValueError('Missing/duplicate snapshots')
    codes={r['code'] for r in references};groups=defaultdict(list);source_rows=0
    for entry in entries:
        path=Path(entry['folder'])/'response.bin';b=path.read_bytes()
        if entry['status']!='INVENTORIED' or hashlib.sha256(b).hexdigest()!=entry['sha256']:raise ValueError('Source integrity failure')
        with zipfile.ZipFile(io.BytesIO(b)) as z:
            with z.open(z.infolist()[0]) as stream:
                for row in csv.DictReader(io.TextIOWrapper(stream,encoding='utf-8-sig',newline='')):
                    source_rows+=1
                    year=int(row['YEAR']);month=int(row['MONTH'])
                    if year!=entry['year'] or month not in range(1,13):raise ValueError('Source period mismatch')
                    origin,dest=row['ORIGIN_COUNTRY'],row['DEST_COUNTRY']
                    code=dest if origin=='US' else origin if dest=='US' else None
                    if code in codes:groups[(code,year,(month-1)//3+1)].append(row)
    results=compare(references,groups)
    summary={'reference_rows':len(references),'countries':sorted({r['country'] for r in references}),
             'source_rows_scanned':source_rows,
             'seats':dict(Counter(r['status_seats'] for r in results)),
             'passengers':dict(Counter(r['status_passengers'] for r in results)),
             'CountAirline_diagnostics':{k:sum(r[k] is not None and Decimal(str(r[k]))==Decimal(str(r['reference_CountAirline'])) for r in results)
                for k in ['F_distinct_operating_airlines','F_distinct_reported_airlines','F_monthly_distinct_sum','F_source_rows','all_classes_source_rows','all_classes_distinct_airlines','diagnostic_rows_times_distinct']}}
    if hashlib.sha256(args.reference.read_bytes()).hexdigest()!=digest:raise ValueError('Reference changed during read')
    out=Path(__file__).resolve().parent/'runs'/('bts-reference-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir(parents=True,exist_ok=False)
    write_csv(out/'comparison.csv',results)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'country-lookup.csv').write_bytes(lookup_bytes)
    manifest={'reference_path':str(args.reference.resolve()),'reference_sha256':digest,'reference_unchanged':True,
              'collection_sha256':hashlib.sha256(collection_bytes).hexdigest(),'source_snapshots':entries,
              'lookup_url':'https://www.transtats.bts.gov/Download_Lookup.asp?Y11x72=Y_Pbhagel_PbQR',
              'lookup_sha256':hashlib.sha256(lookup_bytes).hexdigest(),'created_utc':datetime.now(timezone.utc).isoformat(),
              'rules':'US country code both directions; primary class F; alternatives diagnostic only',
              'data_mutations':False,'network_calls':0,'scope':'BTS seats/passengers/count diagnostic; no trade validation'}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'output':str(out),'summary':summary},indent=2))

if __name__=='__main__':run()
