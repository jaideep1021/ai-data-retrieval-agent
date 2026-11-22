import json
import unittest
from census_trade_example import parse_response
class CensusTests(unittest.TestCase):
    def raw(self,value='790131049',period='2020-01',country='7910'):
        return json.dumps([['CTY_NAME','GEN_VAL_MO','time','CTY_CODE'],['SOUTH AFRICA',value,period,country]]).encode()
    def test_exact_and_rounded(self):
        r=parse_response(self.raw(),'GEN_VAL_MO','7910','2020-01')
        self.assertEqual(r['value_usd'],'790131049');self.assertEqual(r['rounded_millions_usd'],'790.1')
    def test_zero_is_valid(self):
        self.assertEqual(parse_response(self.raw('0'),'GEN_VAL_MO','7910','2020-01')['value_usd'],'0')
    def test_missing_negative_wrong_period_and_country(self):
        for raw in [self.raw(None),self.raw('-1'),self.raw(period='2020-02'),self.raw(country='0000')]:
            with self.assertRaises(ValueError):parse_response(raw,'GEN_VAL_MO','7910','2020-01')
    def test_errors_and_multiple_rows(self):
        data=json.loads(self.raw());data.append(data[1])
        for raw in [b'',b'<html>Missing Key</html>',json.dumps(data).encode(),b'{}']:
            with self.assertRaises(ValueError):parse_response(raw,'GEN_VAL_MO','7910','2020-01')
