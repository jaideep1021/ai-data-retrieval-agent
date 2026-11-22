import io,zipfile,unittest
from process_tourism_ratios import parse_bulk

def bundle(lines):
 b=io.BytesIO()
 with zipfile.ZipFile(b,'w') as z:z.writestr('API_test.csv',lines)
 return b.getvalue()
class BulkTests(unittest.TestCase):
 def test_zero_missing_and_absent_year(self):
  raw=bundle('"Country Name","Country Code","Indicator Name","Indicator Code","2015","2020"\n"Kenya","KEN","Test","X","0",""\n')
  r=parse_bulk(raw,'X',['Kenya']);self.assertEqual(r[0]['value'],0);self.assertIsNone(r[5]['value']);self.assertEqual(r[-1]['status'],'YEAR_NOT_IN_DOWNLOAD')
 def test_wrong_indicator(self):
  with self.assertRaises(ValueError):parse_bulk(bundle('"Country Name","Indicator Code"\n"Kenya","Y"\n'),'X',['Kenya'])
 def test_duplicate(self):
  with self.assertRaises(ValueError):parse_bulk(bundle('"Country Name","Indicator Code"\n"Kenya","X"\n"Kenya","X"\n'),'X',['Kenya'])
 def test_missing_country(self):
  with self.assertRaises(ValueError):parse_bulk(bundle('"Country Name","Indicator Code"\n"Ghana","X"\n'),'X',['Kenya'])
 def test_alias_and_no_percent_scaling(self):
  r=parse_bulk(bundle('"Country Name","Indicator Code","2020"\n"Cabo Verde","X","39.9"\n'),'X',['Cape Verde']);self.assertEqual(r[5]['value'],39.9)
