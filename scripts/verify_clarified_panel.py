"""Rebuild privately, compare outputs, then check the Excel export read-only."""
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from apply_panel_decisions import build  # noqa: E402


def verify(folder):
    with tempfile.TemporaryDirectory() as temporary:
        rebuilt = Path(temporary) / 'rebuilt'
        build(rebuilt)
        for name in ['workbook-data.json', 'panel.csv', 'missing-values.csv']:
            if (rebuilt / name).read_bytes() != (folder / name).read_bytes():
                raise ValueError('Rebuild differs: ' + name)
    data = json.loads((folder / 'workbook-data.json').read_text())
    excel = folder / 'outputs/review/Africa-clarified-extension.xlsx'
    workbook = openpyxl.load_workbook(excel, read_only=True, data_only=False)
    if workbook.sheetnames != [s['name'] for s in data['sheets']]:
        raise ValueError('Unexpected workbook sheets')
    cells = 0
    for item in data['sheets']:
        headers = list(item['rows'][0])
        expected = [headers] + [[r[k] for k in headers] for r in item['rows']]
        actual = list(workbook[item['name']].values)
        if len(actual) != len(expected):
            raise ValueError('Excel row count differs')
        for a, b in zip(expected, actual):
            if len(a) != len(b):
                raise ValueError('Excel column count differs')
            for x, y in zip(a, b):
                same = x == y or (isinstance(x, (int, float)) and isinstance(y, (int, float))
                                  and math.isclose(x, y, rel_tol=1e-14, abs_tol=1e-12))
                if not same:
                    raise ValueError(f'Excel value mismatch: {x!r} != {y!r}')
                cells += 1
    workbook.close()
    rates = {}
    for row in data['sheets'][0]['rows']:
        rates.setdefault((row['year'], row['quarter']), set()).add(row['US_unemployment_SA_quarter_mean_pct'])
    if any(len(v) != 1 for v in rates.values()) or rates[2025, 4] != {None}:
        raise ValueError('US rate alignment or missing-quarter guard failed')
    result = {'rebuild_exact': True, 'excel_cells_verified': cells,
              'US_quarter_alignment': True, 'Q4_2025_missing_preserved': True,
              'xlsx_sha256': hashlib.sha256(excel.read_bytes()).hexdigest()}
    (folder / 'excel-validation.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    verify(ROOT / 'runs/clarified-panel-20261123')
