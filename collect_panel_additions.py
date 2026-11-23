"""Collect official unemployment and PPP snapshots without keys or paid APIs.

The modeled ILO response is preserved for comparison only. It must not fill
national-estimate gaps. Parsing/quarterly transformations are performed by
apply_panel_decisions.py after download validation.
"""
import argparse
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def collect(out):
    out.mkdir(parents=True, exist_ok=False)
    countries = json.loads((ROOT / 'config/africa-panel-countries.json').read_text())['countries']
    codes = ';'.join(c['bts_code'] for c in countries)
    jobs = [(code, f'https://api.worldbank.org/v2/country/{codes}/indicator/{code}?format=json&per_page=1000&date=2020:2026')
            for code in ['SL.UEM.TOTL.NE.ZS', 'SL.UEM.TOTL.ZS', 'PA.NUS.PRVT.PP']]
    jobs += [(f'bls-{start}', f'https://api.bls.gov/publicAPI/v2/timeseries/data/LNS14000000?startyear={start}&endyear={end}')
             for start, end in [(2020, 2023), (2024, 2026)]]
    manifest = []
    for name, url in jobs:
        entry = dict(name=name, url=url, retrieved_utc=datetime.now(timezone.utc).isoformat())
        try:
            with urllib.request.urlopen(url, timeout=45) as response:
                raw = response.read(12_000_001)
                entry['http_status'] = response.status
            if len(raw) > 12_000_000:
                raise ValueError('Response exceeds the bounded size limit')
            (out / (name + '.json')).write_bytes(raw)
            entry.update(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
            json.loads(raw)  # Reject HTML/service errors even when HTTP is 200.
        except Exception as error:
            entry['error'] = str(error)
        manifest.append(entry)
        (out / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    if any('error' in entry for entry in manifest):
        raise RuntimeError('Some downloads failed; inspect the preserved manifest')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    collect(parser.parse_args().out)
