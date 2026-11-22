"""Provisional BTS example, not an approved mapping to the historical panel.

Downloads the official form export, preserves bytes before parsing, and reports
observed class-F bilateral totals for a selected development country. Missing months never become zero. Uses
only the Python standard library; no search or language-model API calls.
"""
import argparse
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
from html.parser import HTMLParser
import http.cookiejar
import io
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request
import zipfile

URL = 'https://www.transtats.bts.gov/DL_SelectFields.aspx?QO_fu146_anzr=Nv4+Pn44vr45&gnoyr_VQ=FJE'
FIELDS = ('DEPARTURES_SCHEDULED DEPARTURES_PERFORMED SEATS PASSENGERS FREIGHT MAIL '
          'DISTANCE UNIQUE_CARRIER AIRLINE_ID UNIQUE_CARRIER_ENTITY ORIGIN_AIRPORT_ID '
          'ORIGIN ORIGIN_COUNTRY DEST_AIRPORT_ID DEST DEST_COUNTRY AIRCRAFT_TYPE '
          'AIRCRAFT_CONFIG YEAR MONTH CLASS').split()
# Explicit development mappings, not the professor's original country sample.
COUNTRIES = {'South Africa': 'ZA', 'Kenya': 'KE'}
MEASURES = ['SEATS', 'PASSENGERS', 'DEPARTURES_PERFORMED']


class HiddenFields(HTMLParser):
    """Read fresh ASP.NET form tokens; never hard-code session state."""
    def __init__(self):
        super().__init__()
        self.fields = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'input' and attrs.get('type') == 'hidden' and attrs.get('name'):
            self.fields[attrs['name']] = attrs.get('value', '')


def parse_export(raw):
    """Reject error pages, unexpected archives, oversized CSVs and schema drift."""
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = archive.infolist()
        if len(members) != 1 or not members[0].filename.lower().endswith('.csv'):
            raise ValueError('Expected exactly one CSV member')
        if members[0].file_size > 20_000_000:
            raise ValueError('CSV exceeds development size limit')
        data = archive.read(members[0])  # CRC checked; no filesystem extraction.
    reader = csv.DictReader(io.StringIO(data.decode('utf-8-sig')))
    if not set(FIELDS).issubset(reader.fieldnames or []):
        raise ValueError('BTS export schema changed')
    return list(reader)


def summarize(rows, year=2020, quarter=1, country="South Africa"):
    """Sum observed detail once; do not certify source completeness or accuracy.

    Class F and country code US are provisional choices. US includes territories
    in this export; that coverage needs confirmation against the original panel.
    Quarterly airline counts use a union, not a sum of monthly distinct counts.
    """
    if quarter not in (1, 2, 3, 4):
        raise ValueError('Invalid quarter')
    country_code = COUNTRIES[country]
    selected, seen = [], set()
    for row in rows:
        if int(row['YEAR']) != year or not 1 <= int(row['MONTH']) <= 12:
            raise ValueError('Unexpected export period')
        key = tuple(row[k] for k in FIELDS if k not in
                    ['DEPARTURES_SCHEDULED', 'DEPARTURES_PERFORMED', 'SEATS',
                     'PASSENGERS', 'FREIGHT', 'MAIL', 'DISTANCE'])
        if key in seen:
            raise ValueError('Duplicate detail key: investigate before aggregation')
        seen.add(key)
        if (int(row['MONTH']) not in range(quarter * 3 - 2, quarter * 3 + 1)
                or row['CLASS'] != 'F'
                or {row['ORIGIN_COUNTRY'], row['DEST_COUNTRY']} != {'US', country_code}):
            continue
        for field in MEASURES:
            value = Decimal(row[field])
            if not value.is_finite() or value < 0:
                raise ValueError('Invalid additive observation')
        if not row['AIRLINE_ID']:
            raise ValueError('Missing airline identity')
        selected.append(row)
    def totals(part):
        return {k: str(sum((Decimal(r[k]) for r in part), Decimal(0))) for k in MEASURES}
    months = sorted({int(r['MONTH']) for r in selected})
    expected = list(range(quarter * 3 - 2, quarter * 3 + 1))
    return {'status': 'PROVISIONAL_OBSERVED_TOTALS', 'year': year, 'quarter': quarter,
            'country': country, 'country_code': country_code,
            'raw_rows': len(rows), 'selected_rows': len(selected), 'months_present': months,
            'source_completeness_confirmed': False, 'historical_definition_confirmed': False,
            'quarter_totals': totals(selected) if months == expected else None,
            'monthly': {str(m): totals([r for r in selected if int(r['MONTH']) == m]) for m in months},
            'direction_totals': {d: totals([r for r in selected if r['ORIGIN_COUNTRY'] == d])
                                 for d in ('US', country_code)} if months == expected else None,
            'distinct_operating_airlines': len({r['AIRLINE_ID'] for r in selected
                                               if Decimal(r['DEPARTURES_PERFORMED']) > 0}) if months == expected else None,
            'carrier_codes': sorted({r['UNIQUE_CARRIER'] for r in selected}),
            'scope': 'US country code (including territories), both directions, class F; no panel append'}


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--country', choices=COUNTRIES, default='South Africa')
    parser.add_argument('--year', type=int, default=2020)
    parser.add_argument('--quarter', type=int, choices=range(1, 5), default=1)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent / 'runs'
    out = root / ('bts-example-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    manifest = {'source_url': URL, 'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
                'filters': {'geography': args.country, 'year': args.year, 'period': 'All'},
                'fields': FIELDS, 'automation': 'researcher-configured official form download',
                'gemini_calls': 0, 'search_api_calls': 0, 'status': 'STARTED'}
    try:
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        with opener.open(URL, timeout=30) as response:
            page = response.read(2_000_001)
        if len(page) > 2_000_000:
            raise ValueError('Form page exceeds size limit')
        (out / 'source-form.html').write_bytes(page)
        form = HiddenFields()
        form.feed(page.decode())
        if '__VIEWSTATE' not in form.fields:
            raise ValueError('Official download form changed')
        params = dict(form.fields, cboGeography=args.country, cboYear=str(args.year),
                      cboPeriod='All', btnDownload='Download')
        params.update({k: 'on' for k in FIELDS})
        with opener.open(URL, urllib.parse.urlencode(params).encode(), timeout=60) as response:
            raw = response.read(20_000_001)
            manifest.update(http_status=response.status, final_url=response.url)
        (out / 'response.bin').write_bytes(raw)
        manifest.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        if len(raw) > 20_000_000:
            raise ValueError('Download exceeds size limit; preserved response is truncated')
        result = summarize(parse_export(raw), args.year, args.quarter, args.country)
        (out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
        manifest['status'] = 'PROVISIONAL_EXAMPLE_COMPLETE'
        print(json.dumps(result, indent=2))
    except Exception as exc:
        manifest.update(status='FAILED', error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        manifest['seconds'] = time.monotonic() - started
        (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        print('Private evidence:', out)


if __name__ == '__main__':
    run()
