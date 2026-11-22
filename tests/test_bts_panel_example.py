"""Offline synthetic cases; these do not establish historical panel accuracy."""
import io
import unittest
import zipfile
from bts_panel_example import FIELDS, parse_export, summarize


def row(month, origin='US', dest='ZA', carrier='1', service='F', **changes):
    data = dict.fromkeys(FIELDS, '0')
    data.update(YEAR='2020', MONTH=str(month), CLASS=service, ORIGIN_COUNTRY=origin,
                DEST_COUNTRY=dest, AIRLINE_ID=carrier, UNIQUE_CARRIER=carrier,
                SEATS='10', PASSENGERS='8', DEPARTURES_PERFORMED='1')
    data.update(changes)
    return data


class BTSExampleTests(unittest.TestCase):
    def test_both_directions_and_distinct_quarter_carriers(self):
        rows = [row(m, origin=o, dest=d) for m in (1, 2, 3)
                for o, d in [('US', 'ZA'), ('ZA', 'US')]]
        result = summarize(rows)
        self.assertEqual(result['quarter_totals']['SEATS'], '60')
        self.assertEqual(result['direction_totals']['US']['SEATS'], '30')
        self.assertEqual(result['distinct_operating_airlines'], 1)
        self.assertFalse(result['source_completeness_confirmed'])

    def test_exclude_wrong_country_class_and_period(self):
        rows = [row(m) for m in (1, 2, 3)]
        rows += [row(4), row(1, dest='KE'), row(1, service='G'), row(1, service='K')]
        self.assertEqual(summarize(rows)['selected_rows'], 3)

    def test_partial_quarter_not_zero(self):
        for rows in ([], [row(1), row(3)]):
            result = summarize(rows)
            self.assertIsNone(result['quarter_totals'])
            self.assertIsNone(result['distinct_operating_airlines'])

    def test_duplicates_bad_period_and_bad_values(self):
        for rows in ([row(1), row(1)], [row(1, YEAR='2019')],
                     [row(1, SEATS='NaN')], [row(1, PASSENGERS='-1')],
                     [row(1, AIRLINE_ID='')]):
            with self.assertRaises(ValueError):
                summarize(rows)

    def test_archive_and_schema_failure(self):
        with self.assertRaises(zipfile.BadZipFile):
            parse_export(b'<html>service unavailable</html>')
        for name, content in [('data.csv', 'WRONG\n1\n'), ('error.html', 'failure')]:
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, 'w') as archive:
                archive.writestr(name, content)
            with self.assertRaises(ValueError):
                parse_export(buffer.getvalue())

    def test_kenya_mapping_does_not_mix_south_africa(self):
        rows = [row(m, origin=o, dest=d) for m in (1, 2, 3)
                for o, d in [('US', 'KE'), ('KE', 'US')]]
        rows += [row(m) for m in (1, 2, 3)]
        result = summarize(rows, country='Kenya')
        self.assertEqual(result['country_code'], 'KE')
        self.assertEqual(result['selected_rows'], 6)
        self.assertEqual(result['quarter_totals']['SEATS'], '60')
        self.assertEqual(result['direction_totals']['KE']['SEATS'], '30')

    def test_valid_archive(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr('data.csv', ','.join(FIELDS) + '\n' +
                             ','.join(row(1)[k] for k in FIELDS) + '\n')
        self.assertEqual(parse_export(buffer.getvalue())[0]['MONTH'], '1')
