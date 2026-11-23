"""Apply the supervisor's clarified definitions to preserved panel inputs.

This offline build never changes a download or the supplied reference. Annual
source values are repeated within their own year, not interpolated. National
unemployment gaps are NOT filled from the separately downloaded modeled series.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ADDITIONS = ROOT / 'runs/supervisor-update-20261123'
BASE = ROOT / 'runs/scheduled-primary-20261122/workbook-data.json'
INCOME = ROOT / 'runs/income-classification-20261120/historical-comparison.csv'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def worldbank_values(payload, indicator, countries):
    """Reject incomplete pages, duplicate keys, wrong series and invalid values."""
    if not isinstance(payload, list) or len(payload) != 2:
        raise ValueError('World Bank response is not a data page')
    meta, rows = payload
    if meta.get('pages') != 1 or meta.get('page') != 1 or meta.get('total') != len(rows):
        raise ValueError('Incomplete World Bank response')
    result = {}
    for row in rows:
        country, year = row['country']['id'], int(row['date'])
        key = country, year
        if row['indicator']['id'] != indicator or country not in countries or not 2020 <= year <= 2026:
            raise ValueError('Unexpected World Bank series, country or year')
        if key in result:
            raise ValueError('Duplicate World Bank country/year')
        value = row['value']
        if value is not None:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError('Invalid World Bank value')
            if indicator.startswith('SL.UEM') and value > 100:
                raise ValueError('Unemployment percentage exceeds 100')
        result[key] = value
    return result


def bls_months(payloads):
    """Use only the requested monthly SA rate; retain real zeros and reject duplicates."""
    result = {}
    for payload in payloads:
        series = payload.get('Results', {}).get('series', [])
        if payload.get('status') != 'REQUEST_SUCCEEDED' or len(series) != 1 or series[0]['seriesID'] != 'LNS14000000':
            raise ValueError('Unexpected or failed BLS response')
        for row in series[0]['data']:
            if row['period'] == 'M13':  # Annual averages must not be counted as a month.
                continue
            month = int(row['period'][1:])
            key = int(row['year']), month
            if not row['period'].startswith('M') or not 1 <= month <= 12 or key in result:
                raise ValueError('Duplicate or invalid BLS month')
            # BLS uses '-' for unavailable observations (e.g. a missed survey).
            # Preserve the month as missing so its quarterly mean also stays missing.
            if row['value'] == '-':
                result[key] = None
                continue
            value = float(row['value'])
            if not math.isfinite(value) or not 0 <= value <= 100:
                raise ValueError('Invalid BLS rate')
            result[key] = value
    return result


def quarter_mean(monthly, year, quarter):
    """A rate is averaged, not summed; require all three source months."""
    values = [monthly.get((year, m)) for m in range(3 * quarter - 2, 3 * quarter + 1)]
    return sum(values) / 3 if all(v is not None for v in values) else None


def nonstop(departures):
    """Positive observed departures prove existence, even in a partial quarter.

    Zero/missing returned records alone do not prove no service, so remain null.
    """
    if departures is None:
        return None
    if isinstance(departures, bool) or not isinstance(departures, (int, float)) or not math.isfinite(departures) or departures < 0:
        raise ValueError('Invalid departure count')
    return 1 if departures > 0 else None


def rename(field):
    """Change approved labels without recalculating the preserved measures."""
    field = field.replace('Nonforeign_carrier_', 'US_carrier_')
    if 'Foreign_carrier_' in field or 'US_carrier_' in field:
        field = field.removesuffix('_candidate')
    return {'ACS_foreign_born_persons_alternative': 'US_residents_born_in_country_persons',
            'EIA_spot_equal_month_mean_USD_gallon_candidate': 'US_EIA_spot_quarter_mean_USD_gallon',
            'BTS_quarter_end_USD_gallon_candidate': 'US_BTS_quarter_end_USD_gallon'}.get(field, field)


def build(out, sources=ADDITIONS):
    base = json.loads(BASE.read_text())
    rows = base['sheets'][0]['rows']
    countries = {r['country_code'] for r in rows}
    expected = {(c, y, q) for c in countries for y in range(2020, 2027)
                for q in range(1, (2 if y == 2026 else 4) + 1)}
    if len(countries) != 14 or len(rows) != 364 or {(r['country_code'], r['year'], r['quarter']) for r in rows} != expected:
        raise ValueError('Base panel does not match the agreed coverage')

    # Verify the registered earlier sources as well as the new response bytes.
    registered = json.loads((ROOT / 'runs/unimputed-baseline-20261120-r3/source-register.json').read_text())
    for entry in registered:
        if digest(ROOT / entry['path']) != entry['sha256']:
            raise ValueError('Changed baseline source: ' + entry['path'])
    manifest = json.loads((sources / 'manifest.json').read_text())
    expected_sources = {'SL.UEM.TOTL.NE.ZS', 'SL.UEM.TOTL.ZS', 'PA.NUS.PRVT.PP', 'bls-2020', 'bls-2024'}
    if len(manifest) != 5 or {entry['name'] for entry in manifest} != expected_sources:
        raise ValueError('Missing or duplicate source entries')
    for entry in manifest:
        if entry.get('error') or entry.get('http_status') != 200 or digest(sources / (entry['name'] + '.json')) != entry['sha256']:
            raise ValueError('Failed or changed new source: ' + entry['name'])
    national = worldbank_values(json.loads((sources / 'SL.UEM.TOTL.NE.ZS.json').read_text()), 'SL.UEM.TOTL.NE.ZS', countries)
    consumption = worldbank_values(json.loads((sources / 'PA.NUS.PRVT.PP.json').read_text()), 'PA.NUS.PRVT.PP', countries)
    monthly = bls_months([json.loads((sources / n).read_text()) for n in ['bls-2020.json', 'bls-2024.json']])
    groups = {}
    with INCOME.open(newline='') as f:
        for r in csv.DictReader(f):
            if r['country'] in groups and groups[r['country']] != r['reference']:
                raise ValueError('Reference income groups are not fixed')
            groups[r['country']] = r['reference']

    removed = {'IncomeGroup_effective_FY_candidate', 'IncomeGroup_source_FY', 'Fuel_Cost_Africa'}
    updated = []
    for old in rows:
        row = {rename(k): v for k, v in old.items() if k not in removed}
        country, year, quarter = old['country_code'], old['year'], old['quarter']
        row.update(IncomeGroup_fixed_reference=groups[old['country_name']],
                   PPP_consumption_LCU_per_international_dollar=consumption.get((country, year)),
                   Destination_unemployment_national_annual_pct=national.get((country, year)),
                   US_unemployment_SA_quarter_mean_pct=quarter_mean(monthly, year, quarter),
                   Nonstop_scheduled_observed=nonstop(old['observed_DEPARTURES_PERFORMED']))
        updated.append(row)

    # Retain existing detailed reasons, updating only labels and superseded fields.
    missing = [{**r, 'field': rename(r['field'])} for r in base['sheets'][1]['rows'] if r['field'] not in removed]
    for row in updated:
        for field, reason in [('PPP_consumption_LCU_per_international_dollar', 'SOURCE_ANNUAL_VALUE_UNAVAILABLE'),
                              ('Destination_unemployment_national_annual_pct', 'NATIONAL_ESTIMATE_UNAVAILABLE_NO_MODELED_FILL'),
                              ('US_unemployment_SA_quarter_mean_pct', 'INCOMPLETE_MONTHLY_COVERAGE'),
                              ('Nonstop_scheduled_observed', 'NO_POSITIVE_DEPARTURE_EVIDENCE_NOT_CONFIRMED_ZERO')]:
            if row[field] is None:
                missing.append(dict(service_view='scheduled_F', country=row['country_name'], year=row['year'], quarter=row['quarter'], field=field, reason=reason))
    notes = [
        ('Coverage', '364 rows: 14 countries, 2020 Q1 through 2026 Q2. This is an extension dataset, not a reconstructed 2009-2019 history.'),
        ('Service scope', 'Scheduled class F is primary. AllServices_ columns retain classes F/G/L/P as comparisons. Distinct airline counts and source-record counts remain separate.'),
        ('Foreign and US', 'Foreign means non-US, not African. US columns rename the previously classified nonforeign values; BTS dated carrier groups and existing coverage gates are unchanged.'),
        ('Fuel', 'US fuel is approved. BTS quarter-end price is the historical-comparable measure; EIA quarterly mean spot price is a different alternative. Both are USD/gallon. The empty destination-fuel placeholder is removed.'),
        ('Immigration', 'ACS estimates count US residents born in each named country, in persons. Margins of error are retained. This is birthplace, not citizenship or all descendants. Missing country categories/years remain blank.'),
        ('Income', 'IncomeGroup_fixed_reference holds each country at its constant label in the supplied 2015-2019 reference. It is not a claim about current income status. The old dated version remains in the prior workbook.'),
        ('GDP and PPP', 'GDP remains the labelled current-USD candidate. GDP PPP conversion factor PA.NUS.PPP remains; PA.NUS.PRVT.PP adds household/NPISH consumption PPP. Both factors are LCU/international dollar, not GDP amounts or exchange rates.'),
        ('Destination unemployment', 'World Bank SL.UEM.TOTL.NE.ZS, national estimate, percent of labor force. Annual values repeat within their source year. Not measured quarterly; country definitions may differ. Modeled ILO values are preserved separately and do not fill gaps.'),
        ('US unemployment', 'BLS LNS14000000, seasonally adjusted, percent of civilian labor force age 16+. Arithmetic mean of all 3 months; same quarterly value for every destination. This is not an employment count.'),
        ('Nonstop', '1 means positive observed scheduled departures on the US-country segments in the quarter. Missing/zero returned departures remain blank without confirmed absence. A partial quarter can establish existence but not complete volume.'),
        ('Missingness', 'No imputation, carry-forward or missing-to-zero conversion. Observed sums can be partial; provisional sums retain the earlier coverage screen. A zero source-record count does not establish zero aviation service.'),
        ('Annual treatment', 'Annual economics, immigration, tourism and national unemployment repeat within year for alignment only, without interpolation. No 2026 annual values are inferred.'),
        ('Remaining limitations', 'AC index and unavailable tourism/immigration/national unemployment remain blank. Historical trade-date discrepancies remain documented, not shifted. GDP/PPP historical definitions and source revisions are not fully reconciled.'),
        ('Provenance', 'Raw downloads, source URLs, UTC retrieval times and hashes are preserved privately. This researcher-configured collection is not an autonomous-agent benchmark.'),
    ]
    for m in manifest:
        notes.append(('Source: ' + m['name'], m['url'] + ' | Retrieved UTC ' + m['retrieved_utc']))
    sheets = [{'name': 'Scheduled main', 'rows': updated}, {'name': 'Missing values', 'rows': missing},
              {'name': 'Notes', 'rows': [{'Topic': a, 'Explanation': b} for a, b in notes]}]
    out.mkdir(parents=True, exist_ok=False)
    (out / 'workbook-data.json').write_text(json.dumps({'sheets': sheets}, allow_nan=False))
    for name, data in [('panel.csv', updated), ('missing-values.csv', missing)]:
        with (out / name).open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(data[0])); writer.writeheader(); writer.writerows(data)
    counts = {f: sum(r[f] is not None for r in updated) for f in updated[0]}
    audit = {'rows': len(updated), 'columns': len(updated[0]), 'countries': len(countries),
             'available_cells_by_field': counts, 'baseline_registered_sources_verified': len(registered),
             'new_sources_verified': len(manifest), 'base_sha256': digest(BASE), 'income_sha256': digest(INCOME),
             'renames': {f: rename(f) for f in rows[0] if f != rename(f)}, 'removed_columns': sorted(removed),
             'retained_values_exact': all(r[rename(f)] == old[f] for r, old in zip(updated, rows) for f in old if f not in removed)}
    (out / 'validation.json').write_text(json.dumps(audit, indent=2))
    (out / 'source-register.json').write_text(json.dumps({'baseline': registered, 'new_sources': manifest,
        'inputs': [{'path': str(p.relative_to(ROOT)), 'sha256': digest(p)} for p in [BASE, INCOME]]}, indent=2))
    print(json.dumps({k: v for k, v in audit.items() if k != 'available_cells_by_field'}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='New output directory; existing folders are never overwritten')
    parser.add_argument('--sources', type=Path, default=ADDITIONS, help='Preserved additional-source snapshot folder')
    args = parser.parse_args()
    build(args.out, args.sources)
