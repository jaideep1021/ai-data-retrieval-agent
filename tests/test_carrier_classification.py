import unittest
from classify_aviation_markets import classify
ROW={'AIRLINE_ID':'1','UNIQUE_CARRIER_ENTITY':'A','YEAR':'2020','MONTH':'2'}
def record(group,start='1/1/2019 12:00:00 AM',end=''):
 return {'CARRIER_GROUP_NEW':group,'START_DATE_SOURCE':start,'THRU_DATE_SOURCE':end}
class ClassificationTests(unittest.TestCase):
 def test_foreign_and_nonforeign(self):
  self.assertIs(classify(ROW,{('1','A'):[record('0')]}),True)
  self.assertIs(classify(ROW,{('1','A'):[record('3')]}),False)
 def test_unmapped_not_defaulted(self):self.assertIsNone(classify(ROW,{}))
 def test_expired_mapping(self):self.assertIsNone(classify(ROW,{('1','A'):[record('0',end='1/31/2020 12:00:00 AM')]}))
 def test_partial_month_not_full(self):self.assertIsNone(classify(ROW,{('1','A'):[record('0',start='2/15/2020 12:00:00 AM')]}))
 def test_conflicting_partial_overlap(self):self.assertIsNone(classify(ROW,{('1','A'):[record('0'),record('3',start='2/15/2020 12:00:00 AM')]}))
 def test_duplicate_names_same_group(self):self.assertIs(classify(ROW,{('1','A'):[record('0'),record('0')]}),True)
