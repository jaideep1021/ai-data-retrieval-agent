"""Collect annual World Bank candidate series without altering the quarterly panel.

PPP here is the GDP conversion factor, a candidate requiring reference review.
Annual observations stay annual: no interpolation or quarterly repetition.
"""
import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
SERIES = ('NY.GDP.MKTP.CD', 'SP.POP.TOTL', 'PA.NUS.PPP', 'PA.NUS.FCRF')

def parse(payload, code, countries):
    """Validate identifiers, one-page coverage and unique country-year records."""
    if not isinstance(payload, list) or len(payload) != 2:
        raise ValueError('Unexpected World Bank response')
    meta, data = payload
    if int(meta['pages']) != 1 or int(meta['total']) != len(data):
        raise ValueError('Incomplete pagination')
    seen = set()
    rows = []
    for r in data:
        country = r['country']['id']; year = int(r['date']); value = r['value']
        key = (country, year)
        if country not in countries or not 2015 <= year <= 2026 or key in seen:
            raise ValueError('Invalid or duplicate country-year')
        if r['indicator']['id'] != code:
            raise ValueError('Wrong indicator')
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))):
            raise ValueError('Invalid value')
        seen.add(key)
        rows.append({'country': countries[country], 'country_code': country,
                     'indicator': code, 'year': year, 'value': value,
                     'status': 'AVAILABLE' if value is not None else 'MISSING',
                     'frequency': 'annual'})
    # Explicit missing rows also cover years omitted entirely by the API.
    for country in countries:
        for year in range(2015, 2027):
            if (country, year) not in seen:
                rows.append({'country': countries[country], 'country_code': country,
                             'indicator': code, 'year': year, 'value': None,
                             'status': 'NOT_RETURNED', 'frequency': 'annual'})
    return rows

def run(folder, series=SERIES):
    folder.mkdir(parents=True, exist_ok=True)
    countries = {r['bts_code']: r['reference_name'] for r in json.loads(
        (ROOT/'config/africa-census-countries.json').read_text())['countries']}
    manifest = {}; rows = []; definitions = {}
    for code in series:
        for kind, url in (
            ('metadata', f'https://api.worldbank.org/v2/indicator/{code}?source=2&format=json'),
            ('data', 'https://api.worldbank.org/v2/country/' + ';'.join(countries) +
             f'/indicator/{code}?source=2&date=2015:2026&format=json&per_page=1000')):
            path = folder/f'{code}-{kind}.json'
            if path.exists():
                raise FileExistsError('Use a new folder to preserve earlier snapshots')
            with urlopen(url, timeout=45) as response:
                raw = response.read(5_000_001)
            if len(raw) > 5_000_000:
                raise ValueError('Response exceeds bound')
            path.write_bytes(raw)
            manifest[path.name] = {'url': url, 'retrieved_utc': datetime.now(timezone.utc).isoformat(),
                                   'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
            (folder/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
            payload = json.loads(raw)
            if kind == 'metadata':
                matches = [r for r in payload[1] if r['id'] == code]
                if len(matches) != 1: raise ValueError('Metadata identifier mismatch')
                definitions[code] = matches[0]
            else:
                rows.extend(parse(payload, code, countries))
        print(code, 'saved', flush=True)
    with (folder/'annual-candidates.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    (folder/'definitions.json').write_text(json.dumps(definitions, indent=2)+'\n')
    summary = {c: {str(y): sum(r['value'] is not None for r in rows if r['indicator']==c and r['year']==y)
                   for y in range(2015, 2027)} for c in series}
    (folder/'availability.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', type=Path, required=True)
    run(parser.parse_args().folder)
