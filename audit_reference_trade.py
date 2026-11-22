"""Read-only trade-field inventory. Patterns are evidence, not field definitions.

Writes private diagnostics; never changes the reference or retrieves trade data.
Requires xlrd from requirements-panel.txt for the legacy XLS workbook.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import xlrd

ROOT = Path(__file__).resolve().parent
FIELDS = ('IYR', 'EYR', 'IQ', 'EQ', 'ExportHi', 'ImportHi')

def validate_mapping(mapping, bts_countries):
    """Prevent missing countries, duplicate identifiers and cross-code confusion."""
    rows = mapping['countries']
    expected = {(r['name'], r['bts_code']) for r in bts_countries['countries']}
    if len(rows) != 14 or {(r['reference_name'], r['bts_code']) for r in rows} != expected:
        raise ValueError('Census mapping does not match the 14-country BTS scope')
    codes = [r['census_code'] for r in rows]
    if any(not isinstance(c, str) or not re.fullmatch(r'\d{4}', c) for c in codes) or len(set(codes)) != 14:
        raise ValueError('Expected 14 unique four-character Census codes')

def run(reference):
    mapping = json.loads((ROOT/'config/africa-census-countries.json').read_text())
    validate_mapping(mapping, json.loads((ROOT/'config/africa-panel-countries.json').read_text()))
    before = hashlib.sha256(reference.read_bytes()).hexdigest()
    workbook = xlrd.open_workbook(reference)
    sheet = workbook.sheet_by_index(0)
    names = sheet.row_values(0)
    rows = [dict(zip(names, sheet.row_values(i))) for i in range(1, sheet.nrows)]
    keys = []
    for r in rows:
        dt = xlrd.xldate_as_datetime(r['yr_qrt'], workbook.datemode)
        if dt.day != 1 or dt.month not in (1,4,7,10):
            raise ValueError('Not a quarter-start date')
        r['year'], r['quarter'] = dt.year, (dt.month-1)//3+1
        keys.append((r['CTYNAME'], r['year'], r['quarter']))
    expected = {(c['reference_name'], y, q) for c in mapping['countries'] for y in range(2015,2020) for q in range(1,5)}
    if len(keys)!=280 or set(keys)!=expected: raise ValueError('Reference grid mismatch')
    summary = {}
    for field in FIELDS:
        values = [r[field] for r in rows if r[field] != '']
        groups = defaultdict(list)
        for r in rows: groups[(r['CTYNAME'],r['year'])].append(r[field])
        summary[field] = {'missing':280-len(values), 'min':min(values), 'max':max(values),
            'unique_values':len(set(values)), 'constant_country_years':sum(len(set(v))==1 for v in groups.values()),
            'total_country_years':len(groups)}
        if field.endswith('Hi'):
            summary[field]['value_counts'] = dict(Counter(values))
            summary[field]['nonbinary_countries'] = sorted({r['CTYNAME'] for r in rows if r[field] not in (0,1)})
    out = ROOT/'runs'/('trade-field-review-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(parents=True)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'reference-trade-values.json').write_text(json.dumps([
        {k:r[k] for k in ('CTYNAME','year','quarter',*FIELDS)} for r in rows],indent=2)+'\n')
    assert hashlib.sha256(reference.read_bytes()).hexdigest()==before
    (out/'manifest.json').write_text(json.dumps({'reference_path':str(reference.resolve()),'reference_sha256':before,
        'created_utc':datetime.now(timezone.utc).isoformat(),'mapping_source':mapping['source_url'],
        'mapping_check_date':mapping['checked_date'],'network_calls':0,'definitions_confirmed':False},indent=2)+'\n')
    print(json.dumps({'output':str(out),'summary':summary},indent=2))

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('reference',type=Path)
    run(p.parse_args().reference)
