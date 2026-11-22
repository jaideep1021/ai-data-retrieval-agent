"""Check that Census identifiers cannot silently change the panel's country scope."""
import copy
import json
import unittest
from audit_reference_trade import ROOT, validate_mapping

class TradeMappingTests(unittest.TestCase):
    def setUp(self):
        self.mapping=json.loads((ROOT/'config/africa-census-countries.json').read_text())
        self.bts=json.loads((ROOT/'config/africa-panel-countries.json').read_text())

    def test_complete_mapping_and_alias(self):
        validate_mapping(self.mapping,self.bts)
        row=next(r for r in self.mapping['countries'] if r['reference_name']=='Cape Verde')
        self.assertEqual((row['census_name'],row['census_code']),('Cabo Verde','7643'))

    def test_missing_country(self):
        self.mapping['countries'].pop()
        with self.assertRaises(ValueError):validate_mapping(self.mapping,self.bts)

    def test_duplicate_code(self):
        self.mapping['countries'][1]['census_code']=self.mapping['countries'][0]['census_code']
        with self.assertRaises(ValueError):validate_mapping(self.mapping,self.bts)

    def test_bts_code_not_census_code(self):
        self.mapping['countries'][0]['census_code']='AO'
        with self.assertRaises(ValueError):validate_mapping(self.mapping,self.bts)

if __name__=='__main__':unittest.main()
