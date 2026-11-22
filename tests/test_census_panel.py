import json
import unittest
from census_trade_panel import parse_batch, build, complete_sum

class PanelTests(unittest.TestCase):
    def fixture(self):
        return [['CTY_CODE','CTY_NAME','YEAR','MONTH','GEN_VAL_MO','GEN_VAL_YR'],['7620','ANGOLA','2015','01','0','0']]
    def test_valid_zero(self):
        self.assertEqual(parse_batch(json.dumps(self.fixture()),'imports',2015,[1],{'7620'})[0]['monthly_usd'],0)
    def test_echoed_identifiers(self):
        r=self.fixture();r[0]+=['YEAR','MONTH','CTY_CODE'];r[1]+=['2015','01','7620']
        self.assertEqual(len(parse_batch(json.dumps(r),'imports',2015,[1],{'7620'})),1)
        r[1][-1]='7910'
        with self.assertRaises(ValueError):parse_batch(json.dumps(r),'imports',2015,[1],{'7620'})
    def test_duplicate(self):
        r=self.fixture();r.append(r[1])
        with self.assertRaises(ValueError):parse_batch(json.dumps(r),'imports',2015,[1],{'7620'})
    def test_wrong_period(self):
        with self.assertRaises(ValueError):parse_batch(json.dumps(self.fixture()),'imports',2016,[1],{'7620'})
    def test_wrong_country(self):
        with self.assertRaises(ValueError):parse_batch(json.dumps(self.fixture()),'imports',2015,[1],{'7910'})
    def test_negative_not_zero(self):
        r=self.fixture();r[1][4]='-999999999'
        with self.assertRaises(ValueError):parse_batch(json.dumps(r),'imports',2015,[1],{'7620'})
    def test_missing_measure(self):
        r=self.fixture();r[1][4]=None
        self.assertIsNone(parse_batch(json.dumps(r),'imports',2015,[1],{'7620'})[0]['monthly_usd'])
        self.assertIsNone(complete_sum([1,None,2],3))
    def test_complete_quarter_and_partial_year(self):
        rows=[{'country_code':'7620','year':2026,'month':m,'flow':f,'monthly_usd':1000000,'ytd_usd':m*1000000} for m in range(1,7) for f in ['imports','exports']]
        q,a,c=build(rows,[{'census_code':'7620','reference_name':'Angola'}])
        self.assertEqual(q[-1]['total_trade_usd_millions'],'6')
        self.assertIsNone(a[-1]['imports_annual_usd_millions'])
        self.assertEqual(a[-1]['imports_in_scope_usd_millions'],'6')
        self.assertEqual(sum(r['status']=='DIFFERENT' for r in c),0)
    def test_incomplete_and_duplicate_batches(self):
        r={'country_code':'7620','year':2015,'month':1,'flow':'imports','monthly_usd':0,'ytd_usd':0}
        q,_,_=build([r],[{'census_code':'7620','reference_name':'Angola'}])
        self.assertIsNone(q[0]['imports_usd_millions']);self.assertEqual(q[0]['coverage'],'MISSING_MONTHS')
        with self.assertRaises(ValueError):build([r,r],[{'census_code':'7620','reference_name':'Angola'}])

if __name__=='__main__':unittest.main()
