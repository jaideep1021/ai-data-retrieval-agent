"""Download one all-geography BTS year and inventory it before country filtering.

Official structured retrieval, not autonomous discovery. Original bytes remain
under ignored runs/. Verified saved downloads are reused without network calls;
--refresh creates a separate snapshot so source revisions do not erase evidence.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import http.cookiejar
import io
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request
import zipfile
from bts_panel_example import URL, FIELDS, HiddenFields

ROOT = Path(__file__).resolve().parent / 'runs' / 'bts-bulk'
MAX_DOWNLOAD = 50_000_000
MAX_CSV = 250_000_000


def inventory(path, year):
    """Inspect all rows without changing them or converting absent rows to zero.

    Month presence is an archive-level observation, not proof that every country
    and carrier reported completely. Country codes are source labels, not a final
    research sample. No service-class filter is applied at this stage.
    """
    months, classes, countries, directions = Counter(), Counter(), set(), Counter()
    seen, duplicates, rows = set(), 0, 0
    dimensions = [k for k in FIELDS if k not in (
        'DEPARTURES_SCHEDULED', 'DEPARTURES_PERFORMED', 'SEATS', 'PASSENGERS',
        'FREIGHT', 'MAIL', 'DISTANCE')]
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if len(entries) != 1 or not entries[0].filename.lower().endswith('.csv'):
            raise ValueError('Expected one CSV archive member')
        if entries[0].file_size > MAX_CSV:
            raise ValueError('Uncompressed CSV exceeds limit')
        with archive.open(entries[0]) as binary:
            reader = csv.DictReader(io.TextIOWrapper(binary, encoding='utf-8-sig', newline=''))
            headers = reader.fieldnames or []
            if len(headers) != len(set(headers)) or not set(FIELDS).issubset(headers):
                raise ValueError('Missing or duplicate export fields')
            for row in reader:
                if None in row or any(row[k] is None for k in FIELDS):
                    raise ValueError('Malformed CSV row')
                if int(row['YEAR']) != year or not 1 <= int(row['MONTH']) <= 12:
                    raise ValueError('Unexpected observation period')
                if not row['ORIGIN_COUNTRY'] or not row['DEST_COUNTRY']:
                    raise ValueError('Missing country code')
                key = tuple(row[k] for k in dimensions)
                duplicates += key in seen
                seen.add(key)
                rows += 1
                months[int(row['MONTH'])] += 1
                classes[row['CLASS']] += 1
                countries.update((row['ORIGIN_COUNTRY'], row['DEST_COUNTRY']))
                direction = ('US_origin' if row['ORIGIN_COUNTRY'] == 'US' else
                             'US_destination' if row['DEST_COUNTRY'] == 'US' else 'neither_US_code')
                directions[direction] += 1
    if not rows:
        raise ValueError('Empty export')
    return {'year': year, 'rows': rows, 'fields': headers,
            'monthly_row_counts': dict(sorted(months.items())),
            'missing_months': sorted(set(range(1, 13)) - months.keys()),
            'service_class_row_counts': dict(sorted(classes.items())),
            'country_codes': sorted(countries), 'country_code_count': len(countries),
            'direction_row_counts': dict(directions), 'duplicate_dimension_keys': duplicates,
            'source_reporting_completeness_confirmed': False,
            'status': 'INVENTORIED_NOT_PANEL_VALIDATED'}


def cached(year):
    """Reuse only a matching successful manifest whose saved bytes still match."""
    for directory in sorted(ROOT.glob(f'{year}-*'), reverse=True):
        try:
            manifest = json.loads((directory / 'manifest.json').read_text())
            if (manifest['status'] != 'INVENTORIED' or manifest['year'] != year
                    or manifest['fields'] != FIELDS or manifest['geography'] != 'All'):
                continue
            raw = directory / 'response.bin'
            if hashlib.sha256(raw.read_bytes()).hexdigest() != manifest['sha256']:
                continue
            inventory(raw, year)  # Recheck the current parser before reuse.
            return directory
        except (OSError, ValueError, KeyError, zipfile.BadZipFile):
            continue
    return None


def download(year, refresh=False):
    """One year per invocation; failures retain their own manifest and snapshot."""
    if not 2015 <= year <= datetime.now(timezone.utc).year:
        raise ValueError('Year must be 2015 through the current year')
    if not refresh:
        previous = cached(year)
        if previous:
            return previous, True
    out = ROOT / f'{year}-{datetime.now(timezone.utc):%Y%m%dT%H%M%S%fZ}'
    out.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    manifest = {'source_url': URL, 'year': year, 'geography': 'All', 'period': 'All',
                'fields': FIELDS, 'started_utc': datetime.now(timezone.utc).isoformat(),
                'status': 'STARTED', 'search_api_calls': 0, 'gemini_calls': 0,
                'method': 'researcher-configured official form download'}
    try:
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        with opener.open(URL, timeout=30) as response:
            page = response.read(2_000_001)
        (out / 'source-form.html').write_bytes(page)
        if len(page) > 2_000_000:
            raise ValueError('Form exceeds limit')
        form = HiddenFields()
        form.feed(page.decode())
        if '__VIEWSTATE' not in form.fields:
            raise ValueError('Official form changed')
        params = dict(form.fields, cboGeography='All', cboYear=str(year),
                      cboPeriod='All', btnDownload='Download')
        params.update({field: 'on' for field in FIELDS})
        # Stream to disk before parsing, retaining partial bytes on interruption.
        sha, size = hashlib.sha256(), 0
        with opener.open(URL, urllib.parse.urlencode(params).encode(), timeout=60) as response:
            manifest.update(http_status=response.status, final_url=response.url,
                            content_type=response.headers.get('Content-Type'))
            with (out / 'response.bin').open('xb') as target:
                while True:
                    chunk = response.read(min(65536, MAX_DOWNLOAD + 1 - size))
                    if not chunk:
                        break
                    target.write(chunk)
                    sha.update(chunk)
                    size += len(chunk)
                    if size > MAX_DOWNLOAD:
                        raise ValueError('Response exceeds download limit; saved bytes are partial')
        manifest.update(bytes=size, sha256=sha.hexdigest(), download_complete=True)
        report = inventory(out / 'response.bin', year)
        (out / 'inventory.json').write_text(json.dumps(report, indent=2) + '\n')
        manifest['status'] = 'INVENTORIED'
    except Exception as exc:
        manifest.update(status='FAILED', error_type=type(exc).__name__, error=str(exc))
        raw = out / 'response.bin'
        if raw.exists():
            manifest.update(preserved_bytes=raw.stat().st_size,
                            preserved_sha256=hashlib.sha256(raw.read_bytes()).hexdigest())
        raise
    finally:
        manifest.update(finished_utc=datetime.now(timezone.utc).isoformat(),
                        seconds=time.monotonic() - start)
        (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return out, False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--year', type=int, required=True)
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    folder, reused = download(args.year, args.refresh)
    print(json.dumps({'evidence_folder': str(folder), 'reused_saved_download': reused,
                      'inventory': json.loads((folder / 'inventory.json').read_text())}, indent=2))
