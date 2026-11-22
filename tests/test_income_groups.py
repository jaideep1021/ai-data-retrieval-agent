import unittest
from income_group_candidates import fiscal_year
class IncomeFiscalYearTests(unittest.TestCase):
 def test_june_cutoff(self):self.assertEqual(fiscal_year(2026,2),2026)
 def test_july_changes_classification(self):self.assertEqual(fiscal_year(2020,3),2021)
 def test_invalid_quarter(self):
  with self.assertRaises(ValueError):fiscal_year(2020,5)
