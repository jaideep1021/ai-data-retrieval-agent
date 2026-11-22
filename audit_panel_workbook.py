"""Read-only workbook inventory for the Africa panel extension.

No downloads, model calls, workbook writes or imputation occur here. Source
values are private: the CLI only writes its JSON inventory under ignored runs/.
This inventory identifies layout, not the economic meaning of a column.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def digest(path):
    """Fingerprint the original bytes, independently of Excel display formats."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inspect_workbook(path, header_row=1):
    """Inventory every sheet, including hidden sheets, without saving the input.

    Formula expressions are counted, never evaluated. A formula is not evidence
    that its cached value is current. Header row is explicit, not guessed from
    the first numeric row. Rich layouts require manual review before ingestion.
    """
    from openpyxl import load_workbook

    path = Path(path)
    if path.suffix.lower() != '.xlsx':
        raise ValueError('Expected an .xlsx workbook')
    if header_row < 1:
        raise ValueError('Header row must be positive')
    before = digest(path)
    book = load_workbook(path, read_only=True, data_only=False, keep_links=False)
    report = {'input_name': path.name, 'sha256': before,
              'audited_at_utc': datetime.now(timezone.utc).isoformat(),
              'mode': 'READ_ONLY_INVENTORY', 'definitions_confirmed': False,
              'formula_values_evaluated': False, 'sheets': []}
    try:
        for sheet in book:
            # Explicitly retain zeroes and distinguish blanks from formula errors.
            rows = list(sheet.iter_rows())
            if header_row > len(rows):
                report['sheets'].append({'sheet': sheet.title, 'state': sheet.sheet_state,
                                         'classification': 'EMPTY_OR_HEADER_NOT_FOUND'})
                continue
            headers = [str(c.value).strip() if c.value is not None else ''
                       for c in rows[header_row - 1]]
            data = [row for row in rows[header_row:] if any(c.value is not None for c in row)]
            counts = Counter(h for h in headers if h)
            duplicate_headers = [h for h, n in counts.items() if n > 1]
            blank_headers = [i + 1 for i, h in enumerate(headers) if not h]
            entry = {'sheet': sheet.title, 'state': sheet.sheet_state,
                     'header_row': header_row, 'headers': headers,
                     'nonempty_data_rows': len(data),
                     'duplicate_headers': duplicate_headers, 'blank_header_columns': blank_headers,
                     'formula_cells': [c.coordinate for row in rows for c in row if c.data_type == 'f'],
                     'error_cells': [c.coordinate for row in rows for c in row if c.data_type == 'e'],
                     'blank_cells_by_column': {str(i + 1): sum(row[i].value is None for row in data)
                                               for i in range(len(headers))},
                     'classification': 'UNCLASSIFIED_REQUIRES_REVIEW'}
            needed = {'Year', 'Month', 'OriginAirportCode', 'DestinationAirportCode',
                      'OriginCountryCode', 'DestinationCountryCode', 'PrimaryAirlineCode',
                      'DepartingSeats', 'Departures'}
            if not duplicate_headers and needed.issubset(headers):
                records = [dict(zip(headers, [c.value for c in row])) for row in data]
                key = ['Year', 'Month', 'OriginAirportCode', 'DestinationAirportCode', 'PrimaryAirlineCode']
                if 'Aircraft' in headers:
                    key.append('Aircraft')
                keys = Counter(tuple(str(r[k]) for k in key) for r in records)
                entry.update(classification='MONTHLY_ROUTE_SAMPLE_NOT_QUARTERLY_PANEL',
                             observed_periods=sorted({f"{r['Year']}-{r['Month']}" for r in records}),
                             duplicate_route_keys=sum(n - 1 for n in keys.values() if n > 1),
                             us_endpoint_rows=sum(str(r['OriginCountryCode']).upper() == 'US' or
                                                  str(r['DestinationCountryCode']).upper() == 'US'
                                                  for r in records),
                             interpretation='No US rows in a sample is not evidence of zero US service. '
                                            'Country code conventions, units and coverage require confirmation.')
            report['sheets'].append(entry)
    finally:
        book.close()
    report['input_bytes_unchanged'] = digest(path) == before
    if not report['input_bytes_unchanged']:
        raise RuntimeError('Input changed during audit; no stable audit can be issued')
    return report


def write_audit(report, output):
    """Keep private inventories under runs and refuse overwriting earlier work."""
    output = Path(output).resolve()
    private_root = Path(__file__).resolve().parent / 'runs'
    if not output.is_relative_to(private_root.resolve()):
        raise ValueError('Output must be inside the project runs/ directory')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--header-row', type=int, default=1)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = inspect_workbook(args.input, args.header_row)
    write_audit(report, args.output)
    print(json.dumps({'output': str(args.output), 'sheets': len(report['sheets']),
                      'input_bytes_unchanged': report['input_bytes_unchanged']}))


if __name__ == '__main__':
    main()
