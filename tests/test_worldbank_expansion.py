import unittest
from validate_worldbank_panel import expand
class ExpansionTests(unittest.TestCase):
    def test_annual_not_divided(self):
        rows=expand([{'country':'Kenya','year':2020,'indicator':'NY.GDP.MKTP.CD','value':'100'}],['Kenya'])
        self.assertEqual([r['GDP_T'] for r in rows[:4]],['100']*4)
        self.assertEqual(len(rows),26)
        self.assertEqual(rows[-1]['quarter'],2)
    def test_missing_not_carried_forward(self):
        rows=expand([{'country':'Kenya','year':2025,'indicator':'SP.POP.TOTL','value':'0'}],['Kenya'])
        self.assertEqual(rows[-3]['Population_T'],'0')
        self.assertIsNone(rows[-1]['Population_T'])
    def test_duplicates_rejected(self):
        r={'country':'Kenya','year':2020,'indicator':'PA.NUS.PPP','value':'1'}
        with self.assertRaises(ValueError):expand([r,r],['Kenya'])
