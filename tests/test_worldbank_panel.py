import unittest
from worldbank_panel import parse

class WorldBankTests(unittest.TestCase):
    def payload(self, value=None):
        return [{'pages':1,'total':1},[{'country':{'id':'KE'},'date':'2020','value':value,'indicator':{'id':'X'}}]]
    def test_missing_stays_missing_and_grid_complete(self):
        rows=parse(self.payload(),'X',{'KE':'Kenya'})
        self.assertEqual(len(rows),12)
        self.assertTrue(all(r['value'] is None for r in rows))
    def test_zero_is_available(self):
        rows=parse(self.payload(0),'X',{'KE':'Kenya'})
        self.assertEqual(next(r for r in rows if r['year']==2020)['status'],'AVAILABLE')
    def test_wrong_indicator(self):
        with self.assertRaises(ValueError):parse(self.payload(),'Y',{'KE':'Kenya'})
    def test_duplicate(self):
        p=self.payload();p[0]['total']=2;p[1]*=2
        with self.assertRaises(ValueError):parse(p,'X',{'KE':'Kenya'})
    def test_pagination(self):
        p=self.payload();p[0]['pages']=2
        with self.assertRaises(ValueError):parse(p,'X',{'KE':'Kenya'})
    def test_wrong_country(self):
        with self.assertRaises(ValueError):parse(self.payload(),'X',{'NG':'Nigeria'})
