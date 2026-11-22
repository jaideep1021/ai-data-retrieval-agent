"""Build two explicitly provisional 14-country views from local BTS snapshots.

No network or overwrite. The reference comparison is a private derived CSV from
compare_bts_reference.py; its manifest ties it to the original workbook. Distinct
counts are retained separately following supervisor guidance. The historical
product remains a diagnostic, not the meaning of source-record count.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile
from bts_quarterly_preview import preview, write_csv

ROOT=Path(__file__).resolve().parent
VARIANTS={'scheduled_F':('F',),'all_returned_classes':('F','G','L','P')}


def split_periods(rows):
    """Partition at the reference boundary, retaining 2026 Q1/Q2 only."""
    if any(r['year']<2015 or r['year']>2026 or (r['year']==2026 and r['quarter']>2) for r in rows):
        raise ValueError('Output outside approved period')
    return [r for r in rows if r['year']<=2019],[r for r in rows if r['year']>=2020]


def retain_counts(row):
    """Expose different units explicitly; zero source rows does not prove zero service.

    DistinctAirlineCount counts reported AIRLINE_ID values in the selected records.
    OperatingAirlineCount restricts them to positive performed departures. Record
    counts are counts of BTS detail rows, not flights, airlines, or the legacy product.
    """
    row['DistinctAirlineCount'] = row['observed_distinct_reported_airlines']
    row['OperatingAirlineCount'] = row['observed_distinct_operating_airlines']
    row['SourceRecordCount'] = row['source_rows']
    row['HistoricalCountProductDiagnostic'] = row['diagnostic_rows_times_reported_airlines']
    row['CountDecision'] = 'RETAIN_DISTINCT_AND_RECORD_COUNTS_SEPARATELY'
    return row


def compare_view(rows, refs):
    """Compare observed sums; preserve empty-selection/reference-zero as its own status."""
    index={(r['country_code'],r['year'],r['quarter']):r for r in rows}
    if len(index)!=len(rows):raise ValueError('Duplicate output key')
    output=[]
    for ref in refs:
        row=index[(ref['code'],int(ref['year']),int(ref['quarter']))]
        result={'country':ref['country'],'code':ref['code'],'year':ref['year'],'quarter':ref['quarter']}
        for field in ('seats','passengers'):
            observed=row['observed_'+field.upper()]; target=Decimal(ref['reference_'+field])
            result['reference_'+field]=str(target)
            result['observed_'+field]=observed
            result['status_'+field]=('NO_ROWS_REFERENCE_ZERO' if target==0 else 'NO_ROWS_REFERENCE_NONZERO') if observed is None else 'EXACT_MATCH' if Decimal(observed)==target else 'DIFFERENT'
        result['reference_CountAirline']=ref['reference_CountAirline']
        result['observed_distinct_reported_airlines']=row['observed_distinct_reported_airlines']
        result['diagnostic_rows_times_reported_airlines']=row['diagnostic_rows_times_reported_airlines']
        for field in ('DistinctAirlineCount','OperatingAirlineCount','SourceRecordCount','HistoricalCountProductDiagnostic'):
            result[field]=retain_counts(dict(row))[field]
        result['approved_CountAirline']=None
        result['CountAirline_definition_status']='BOTH_COUNTS_RETAINED_REFERENCE_UNCHANGED'
        output.append(result)
    return output


def run():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collection',type=Path,required=True)
    parser.add_argument('--comparison-folder',type=Path,required=True)
    parser.add_argument('--countries',type=Path,default=ROOT/'config/africa-panel-countries.json')
    args=parser.parse_args()
    config=json.loads(args.countries.read_text());countries=config['countries'];codes=[r['bts_code'] for r in countries]
    if len(codes)!=14 or len(set(codes))!=14:raise ValueError('Expected 14 distinct countries')
    names={r['bts_code']:r['name'] for r in countries}
    comparison_bytes=(args.comparison_folder/'comparison.csv').read_bytes()
    refs=list(csv.DictReader(io.StringIO(comparison_bytes.decode())))
    refmanifest=json.loads((args.comparison_folder/'manifest.json').read_text())
    refpath=Path(refmanifest['reference_path'])
    if hashlib.sha256(refpath.read_bytes()).hexdigest()!=refmanifest['reference_sha256']:raise ValueError('Reference changed')
    expected={(c,y,q) for c in codes for y in range(2015,2020) for q in range(1,5)}
    if len(refs)!=280 or {(r['code'],int(r['year']),int(r['quarter'])) for r in refs}!=expected:raise ValueError('Reference grid mismatch')
    if any(names[r['code']]!=r['country'] for r in refs):raise ValueError('Country naming mismatch')
    collection_bytes=args.collection.read_bytes();collection=json.loads(collection_bytes)
    entries=collection['years']
    if sorted(e['year'] for e in entries)!=list(range(2015,2027)):raise ValueError('Source years missing or duplicated')
    records=[]
    for e in sorted(entries,key=lambda r:r['year']):
        p=Path(e['folder'])/'response.bin'
        if e['status']!='INVENTORIED' or hashlib.sha256(p.read_bytes()).hexdigest()!=e['sha256']:raise ValueError('Source snapshot changed')
        with zipfile.ZipFile(p) as z:
            members=z.infolist()
            if len(members)!=1 or members[0].file_size>250_000_000:raise ValueError('Invalid archive')
            with z.open(members[0]) as stream:
                for number,row in enumerate(csv.DictReader(io.TextIOWrapper(stream,encoding='utf-8-sig',newline='')),1):
                    # Only retain target bilateral records in memory; raw snapshots remain intact.
                    o,d=row['ORIGIN_COUNTRY'],row['DEST_COUNTRY']
                    if (o=='US' and d in codes) or (d=='US' and o in codes):
                        if row['CLASS'] not in {'F','G','L','P'}:raise ValueError('Unexpected service class; review before extending rules')
                        records.append((e['year'],number,row))
    out=ROOT/'runs'/('bts-panel14-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir(parents=True,exist_ok=False)
    summary={}
    for variant,classes in VARIANTS.items():
        rows,lineage,audit=preview(records,codes,service_classes=classes)
        for row in rows:
            retain_counts(row)
            row['country_name']=names[row['country_code']]
            row['distinct_operating_airlines_three_month_screen']=row.pop('provisional_CountAirline')
            row['approved_CountAirline']=None
            row['definition_status']='BOTH_COUNTS_RETAINED_SERVICE_SCOPE_PROVISIONAL'
        history,extension=split_periods(rows)
        if len(rows)!=644 or len(history)!=280 or len(extension)!=364:raise ValueError('Unexpected grid dimensions')
        comparisons=compare_view(history,refs)
        folder=out/variant;folder.mkdir()
        for name,data in [('historical-preview',history),('extension-preview',extension),('reference-comparison',comparisons),('source-lineage',lineage)]:
            write_csv(folder/(name+'.csv'),data)
        summary[variant]={'historical_rows':len(history),'extension_rows':len(extension),
            'extension_status_counts':dict(Counter(r['status'] for r in extension)),
            'historical_seats':dict(Counter(r['status_seats'] for r in comparisons)),
            'historical_passengers':dict(Counter(r['status_passengers'] for r in comparisons)),
            'audit_target_country_records_only':audit}
    manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'reference_sha256':refmanifest['reference_sha256'],
              'comparison_sha256':hashlib.sha256(comparison_bytes).hexdigest(),'comparison_folder':str(args.comparison_folder.resolve()),
              'country_config':config,'country_config_sha256':hashlib.sha256(args.countries.read_bytes()).hexdigest(),
              'collection_sha256':hashlib.sha256(collection_bytes).hexdigest(),'source_snapshots':entries,
              'variants':VARIANTS,'cutoff':'2026-06','network_calls':0,'approved_CountAirline':None,
              'count_decision':'Retain distinct airlines and source-record counts separately; keep reference product diagnostic and historical values unchanged',
              'note':'All-class historical observed sums can match while conservative three-month-screen totals remain blank. Neither view is approved final data.'}
    if hashlib.sha256(refpath.read_bytes()).hexdigest()!=refmanifest['reference_sha256']:raise ValueError('Reference changed during run')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({'output':str(out),'summary':summary},indent=2))

if __name__=='__main__':run()
