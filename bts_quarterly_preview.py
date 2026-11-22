"""Offline, provisional country-quarter preview from preserved BTS snapshots.

No downloads, imputation or final historical mapping. Class F, US country code
(including territories), both directions and positive performed departures for
carrier qualification are explicit development rules, not validated definitions.
"""
import argparse
from collections import defaultdict
import csv
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import zipfile

MEASURES = ['SEATS', 'PASSENGERS', 'DEPARTURES_SCHEDULED', 'DEPARTURES_PERFORMED', 'FREIGHT', 'MAIL']
ROOT = Path(__file__).resolve().parent


def numeric(value):
    """Reject missing, negative and nonfinite observations rather than filling them."""
    try:
        number = Decimal(value)
    except (InvalidOperation, TypeError) as exc:
        raise ValueError('Invalid numeric observation') from exc
    if not number.is_finite() or number < 0:
        raise ValueError('Negative or nonfinite observation')
    return number


def preview(records, countries, start_year=2015, end_year=2026, end_month=6, service_classes=("F",)):
    """Group source detail, keeping absent months distinct from observed zeros.

    Every input record is (snapshot year, CSV record number, row dictionary).
    Return a full requested country-quarter grid and source-row lineage. Observed
    sums remain visible for incomplete quarters, but proposed quarter totals are
    blank unless all three months have qualifying rows. That is only a presence
    screen, not proof of complete reporting.
    """
    if not service_classes or not set(service_classes).issubset({'F','G','L','P'}):
        raise ValueError('Unsupported or empty service-class selection')
    if not countries or len(countries) != len(set(countries)) or 'US' in countries:
        raise ValueError('Provide distinct non-US country codes')
    if start_year > end_year or end_month not in (3, 6, 9, 12):
        raise ValueError('Expected chronological range ending at a quarter boundary')
    groups = defaultdict(list)
    lineage = []
    audit = {'input_rows': 0, 'after_cutoff_rows': 0, 'selected_rows': 0,
             'passengers_above_seats_rows': 0, 'noninteger_count_rows': 0}
    keys = set()
    for snapshot_year, row_number, row in records:
        audit['input_rows'] += 1
        year, month = int(row['YEAR']), int(row['MONTH'])
        if year != snapshot_year or not 1 <= month <= 12:
            raise ValueError('Snapshot/observation period mismatch')
        if year > end_year or (year == end_year and month > end_month):
            audit['after_cutoff_rows'] += 1
            continue
        if year < start_year or row['CLASS'] not in service_classes:
            continue
        origin, dest = row['ORIGIN_COUNTRY'], row['DEST_COUNTRY']
        country = dest if origin == 'US' else origin if dest == 'US' else None
        if country not in countries:
            continue
        # Retain aircraft and carrier-entity dimensions so valid details are not collapsed.
        key = tuple(row[k] for k in ('YEAR', 'MONTH', 'CLASS', 'UNIQUE_CARRIER_ENTITY',
                    'AIRLINE_ID', 'ORIGIN_AIRPORT_ID', 'DEST_AIRPORT_ID', 'AIRCRAFT_TYPE', 'AIRCRAFT_CONFIG'))
        if key in keys:
            raise ValueError('Duplicate selected segment key')
        keys.add(key)
        values = {field: numeric(row[field]) for field in MEASURES}
        numeric(row['DISTANCE'])  # Validate route value, but do not invent a country aggregate.
        if not row['AIRLINE_ID'].strip():
            raise ValueError('Missing airline identifier')
        audit['passengers_above_seats_rows'] += values['PASSENGERS'] > values['SEATS']
        audit['noninteger_count_rows'] += any(values[k] != values[k].to_integral_value()
                                             for k in MEASURES[:4])
        quarter = (month - 1) // 3 + 1
        direction = 'US_to_country' if origin == 'US' else 'country_to_US'
        groups[country, year, quarter].append((month, direction, row['AIRLINE_ID'], values))
        lineage.append({'country_code': country, 'year': year, 'quarter': quarter,
                        'month': month, 'direction': direction, 'service_class': row['CLASS'], 'source_year': snapshot_year,
                        'csv_record_number': row_number, 'origin': row['ORIGIN'], 'destination': row['DEST'],
                        'airline_id': row['AIRLINE_ID'], **{k: str(v) for k,v in values.items()}})
        audit['selected_rows'] += 1
    output = []
    for country in countries:
        for year in range(start_year, end_year + 1):
            for quarter in range(1, (end_month // 3 if year == end_year else 4) + 1):
                selected = groups[country, year, quarter]
                months = sorted({r[0] for r in selected})
                expected = list(range(quarter * 3 - 2, quarter * 3 + 1))
                full = months == expected
                result = {'country_code': country, 'year': year, 'quarter': quarter,
                          'status': 'PROVISIONAL_THREE_MONTHS_PRESENT' if full else
                                    'NO_SELECTED_RECORDS' if not selected else 'PARTIAL_MONTH_PRESENCE',
                          'months_present': ','.join(map(str, months)), 'source_rows': len(selected),
                          'source_completeness_confirmed': False, 'reference_validated': False}
                for field in MEASURES:
                    observed = str(sum((r[3][field] for r in selected), Decimal(0))) if selected else None
                    result['observed_' + field] = observed
                    result['provisional_' + field] = observed if full else None
                result['observed_distinct_operating_airlines'] = len({r[2] for r in selected if r[3]['DEPARTURES_PERFORMED'] > 0}) if selected else None
                result['observed_distinct_reported_airlines'] = len({r[2] for r in selected}) if selected else None
                result['diagnostic_rows_times_reported_airlines'] = len(selected)*len({r[2] for r in selected}) if selected else None
                result['service_classes'] = ','.join(sorted(service_classes))
                result['provisional_CountAirline'] = len({r[2] for r in selected
                    if r[3]['DEPARTURES_PERFORMED'] > 0}) if full else None
                for direction in ('US_to_country', 'country_to_US'):
                    result[direction + '_months'] = ','.join(map(str,sorted({r[0] for r in selected if r[1]==direction})))
                output.append(result)
    return output, lineage, audit


def write_csv(path, rows):
    """Write explicit blanks for None; never convert unavailable values to zero."""
    if not rows:
        path.write_text('')
        return
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collection', type=Path, required=True)
    parser.add_argument('--countries', nargs='+', required=True)
    args = parser.parse_args()
    collection_bytes = args.collection.read_bytes()
    collection = json.loads(collection_bytes)
    entries = collection['years']
    if sorted(r['year'] for r in entries) != list(range(2015,2027)):
        raise ValueError('Preview requires one snapshot for every year 2015–2026')
    out = ROOT / 'runs' / ('bts-preview-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(parents=True, exist_ok=False)
    manifest = {'status':'STARTED', 'countries':args.countries, 'start_year':2015,
                'analysis_cutoff':'2026-06', 'service_class':'F', 'directions':'both',
                'US_scope':'BTS US country code including territories',
                'airline_rule':'distinct AIRLINE_ID with positive DEPARTURES_PERFORMED',
                'collection':str(args.collection.resolve()),
                'collection_sha256':hashlib.sha256(collection_bytes).hexdigest(),
                'source_snapshots':entries, 'created_utc':datetime.now(timezone.utc).isoformat(),
                'network_calls':0, 'reference_validated':False}
    def records():
        for entry in sorted(entries,key=lambda r:r['year']):
            path = Path(entry['folder']) / 'response.bin'
            if entry['status'] != 'INVENTORIED' or hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:
                raise ValueError('Unverified or changed source snapshot')
            with zipfile.ZipFile(path) as archive:
                members=archive.infolist()
                if len(members)!=1 or members[0].file_size>250_000_000:
                    raise ValueError('Unexpected archive structure or size')
                with archive.open(members[0]) as stream:
                    reader=csv.DictReader(io.TextIOWrapper(stream,encoding='utf-8-sig',newline=''))
                    for number,row in enumerate(reader,1):
                        yield entry['year'],number,row
    try:
        rows,lineage,audit=preview(records(),args.countries)
        write_csv(out/'quarterly-preview.csv',rows)
        write_csv(out/'selected-source-rows.csv',lineage)
        audit['quarterly_rows']=len(rows)
        audit['status_counts']={s:sum(r['status']==s for r in rows) for s in sorted({r['status'] for r in rows})}
        (out/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
        manifest['status']='PROVISIONAL_PREVIEW_COMPLETE'
        print(json.dumps({'output':str(out),'audit':audit},indent=2))
    except Exception as exc:
        manifest.update(status='FAILED',error_type=type(exc).__name__,error=str(exc))
        raise
    finally:
        (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

if __name__=='__main__':
    run()
