"""Aggregation failure paths using synthetic values only; no network requests."""
import unittest
from panel_validation import complete_quarter


def rows(values):
    return [{'year': 2026, 'month': i + 7, 'value': value, 'coverage_complete': True}
            for i, value in enumerate(values)]


class QuarterValidationTests(unittest.TestCase):
    def test_exact_sum_including_observed_zero(self):
        result = complete_quarter(rows(['0.1', '0.2', 0]), 2026, 3)
        self.assertEqual(result['value'], '0.3')
        self.assertEqual(result['status'], 'COMPLETE')

    def test_missing_september_cannot_be_full_quarter(self):
        result = complete_quarter(rows([10, 20]), 2026, 3)
        self.assertIsNone(result['value'])
        self.assertEqual(result['missing_months'], [9])

    def test_blank_and_incomplete_coverage_are_not_zero(self):
        data = rows([10, None, 20])
        self.assertIsNone(complete_quarter(data, 2026, 3)['value'])
        data = rows([10, 0, 20]); data[1]['coverage_complete'] = False
        self.assertIsNone(complete_quarter(data, 2026, 3)['value'])
        self.assertIsNone(complete_quarter([], 2026, 3)['value'])

    def test_duplicate_and_out_of_period_rows_raise(self):
        data = rows([1, 2, 3])
        with self.assertRaises(ValueError):
            complete_quarter(data + [data[0]], 2026, 3)
        with self.assertRaises(ValueError):
            complete_quarter(data, 2026, 4)

    def test_invalid_numbers_and_quarters_raise(self):
        for value in ['NaN', 'Infinity', 'unknown', True]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                complete_quarter(rows([1, value, 3]), 2026, 3)
        with self.assertRaises(ValueError):
            complete_quarter([], 2026, 5)
