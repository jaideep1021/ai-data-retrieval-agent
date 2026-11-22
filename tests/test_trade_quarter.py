import unittest
from census_trade_quarter_check import sum_complete_quarter, MONTHS

class QuarterTests(unittest.TestCase):
    def setUp(self):
        self.rows=[{'period':p,'country_code':'7620','source_field':'GEN_VAL_MO','value_usd':str(i)} for i,p in enumerate(MONTHS)]
    def test_sum_including_zero(self):self.assertEqual(sum_complete_quarter(self.rows),3)
    def test_missing_month(self):
        with self.assertRaises(ValueError):sum_complete_quarter(self.rows[:2])
    def test_duplicate_month(self):
        self.rows[2]['period']=MONTHS[0]
        with self.assertRaises(ValueError):sum_complete_quarter(self.rows)
    def test_mixed_country(self):
        self.rows[2]['country_code']='7910'
        with self.assertRaises(ValueError):sum_complete_quarter(self.rows)
    def test_mixed_flow(self):
        self.rows[2]['source_field']='ALL_VAL_MO'
        with self.assertRaises(ValueError):sum_complete_quarter(self.rows)

if __name__=='__main__':unittest.main()
