"""Offline checks for already normalized monthly additive panel observations.

This is not a BTS/Census downloader or a source-definition mapper. Callers must
first filter and aggregate source records to ONE row per month for ONE country,
variable, unit and definition. No missing values are replaced or estimated.
"""
from decimal import Decimal, InvalidOperation


def complete_quarter(rows, year, quarter):
    """Return an exact sum only when all three months have observed numeric values.

    Rows contain year, month, value and coverage_complete. Completeness must come
    from the source download/coverage check, not the presence of a row alone.
    Empty or partial input returns a missing value; duplicate or out-of-period
    rows are errors rather than opportunities to silently double-count.
    Output decimals are strings to avoid binary floating-point rounding.
    """
    if type(year) is not int or type(quarter) is not int or quarter not in (1, 2, 3, 4):
        raise ValueError('Expected integer year and quarter from 1 to 4')
    expected = set(range(quarter * 3 - 2, quarter * 3 + 1))
    values, incomplete = {}, []
    for row in rows:
        month = row['month']
        if type(month) is not int or row['year'] != year or month not in expected:
            raise ValueError('Row outside the requested quarter')
        if month in values:
            raise ValueError('Duplicate month: normalize source detail before summing')
        raw = row.get('value')
        values[month] = None
        if raw is None or raw == '' or row.get('coverage_complete') is not True:
            incomplete.append(month)
            continue
        if isinstance(raw, bool):
            raise ValueError('Boolean is not a numeric observation')
        try:
            value = Decimal(str(raw))
        except InvalidOperation as exc:
            raise ValueError('Invalid numeric observation') from exc
        if not value.is_finite():
            raise ValueError('Nonfinite numeric observation')
        values[month] = value
    missing = sorted(expected - values.keys())
    if missing or incomplete:
        return {'value': None, 'status': 'INCOMPLETE_QUARTER',
                'missing_months': missing, 'unusable_months': sorted(incomplete)}
    return {'value': str(sum(values.values(), Decimal(0))), 'status': 'COMPLETE',
            'missing_months': [], 'unusable_months': []}
