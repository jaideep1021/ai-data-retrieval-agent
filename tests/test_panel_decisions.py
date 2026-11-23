"""Protect missing-data, source identity and period aggregation decisions."""
import unittest
from apply_panel_decisions import bls_months, nonstop, quarter_mean, rename, worldbank_values


def wb(rows):
    return [{'pages': 1, 'page': 1, 'total': len(rows)}, rows]


def record(value=4.5):
    return {'country': {'id': 'KE'}, 'date': '2025', 'value': value,
            'indicator': {'id': 'SL.UEM.TOTL.NE.ZS'}}


def bls(rows, series='LNS14000000'):
    return {'status': 'REQUEST_SUCCEEDED', 'Results': {'series': [{'seriesID': series, 'data': rows}]}}


class PanelDecisionsTests(unittest.TestCase):
    def test_wb_null_is_missing_zero_is_value(self):
        self.assertIsNone(worldbank_values(wb([record(None)]), 'SL.UEM.TOTL.NE.ZS', {'KE'})['KE', 2025])
        self.assertEqual(worldbank_values(wb([record(0)]), 'SL.UEM.TOTL.NE.ZS', {'KE'})['KE', 2025], 0)

    def test_wb_rejects_duplicate_keys(self):
        with self.assertRaises(ValueError):
            worldbank_values(wb([record(), record()]), 'SL.UEM.TOTL.NE.ZS', {'KE'})

    def test_wb_rejects_incomplete_pages(self):
        data = wb([record()]); data[0]['pages'] = 2
        with self.assertRaises(ValueError):
            worldbank_values(data, 'SL.UEM.TOTL.NE.ZS', {'KE'})

    def test_wb_rejects_wrong_series_country_and_invalid_rates(self):
        for rows, code, countries in [([record()], 'other', {'KE'}), ([record()], 'SL.UEM.TOTL.NE.ZS', {'NG'}),
                                        ([record(101)], 'SL.UEM.TOTL.NE.ZS', {'KE'}), ([record(float('nan'))], 'SL.UEM.TOTL.NE.ZS', {'KE'})]:
            with self.assertRaises(ValueError):
                worldbank_values(wb(rows), code, countries)

    def test_bls_unavailable_month_not_zero(self):
        monthly = bls_months([bls([{'year': '2025', 'period': 'M10', 'value': '-'}])])
        self.assertIn((2025, 10), monthly)
        self.assertIsNone(monthly[2025, 10])

    def test_bls_rejects_duplicate_and_wrong_series(self):
        row = {'year': '2025', 'period': 'M01', 'value': '4.0'}
        for data in [bls([row, row]), bls([row], 'wrong')]:
            with self.assertRaises(ValueError):
                bls_months([data])

    def test_annual_average_is_not_a_month(self):
        self.assertEqual(bls_months([bls([{'year': '2025', 'period': 'M13', 'value': '4'}])]), {})

    def test_quarter_mean_not_sum(self):
        self.assertEqual(quarter_mean({(2025, 1): 3, (2025, 2): 4, (2025, 3): 5}, 2025, 1), 4)

    def test_incomplete_quarter_missing(self):
        self.assertIsNone(quarter_mean({(2025, 11): 4, (2025, 12): 5}, 2025, 4))
        self.assertIsNone(quarter_mean({(2025, 10): None, (2025, 11): 4, (2025, 12): 5}, 2025, 4))

    def test_nonstop_zero_is_not_proven_absence(self):
        self.assertEqual(nonstop(1), 1)
        self.assertIsNone(nonstop(0))
        self.assertIsNone(nonstop(None))
        with self.assertRaises(ValueError):
            nonstop(-1)

    def test_labels_do_not_conflate_foreign_and_african(self):
        self.assertEqual(rename('AllServices_Nonforeign_carrier_seats_candidate'), 'AllServices_US_carrier_seats')
        self.assertEqual(rename('Foreign_carrier_seats_candidate'), 'Foreign_carrier_seats')


if __name__ == '__main__':
    unittest.main()
