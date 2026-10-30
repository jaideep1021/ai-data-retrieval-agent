"""Public sample contracts: determinism, validation and offline provenance."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import prepare_business_data as business


def rows():
    return [{'year':'2024','quarter':'4','citymarketid_1':str(30000+i),
             'citymarketid_2':str(40000+i),'city1':'Example A','city2':'Example B',
             'nsmiles':'500','passengers':'100.12345','fare':'200.1234567',
             'carrier_lg':'AA','large_ms':'0.6','fare_lg':'210.1234567',
             'carrier_low':'BB','lf_ms':'0.2','fare_low':'180.1234567'} for i in range(40)]


class BusinessDataTests(unittest.TestCase):
    def test_deterministic_independent_of_source_row_order(self):
        sample=business.make_sample(rows())
        self.assertEqual(sample,business.make_sample(list(reversed(rows()))))
        self.assertEqual(len(sample),30)
        self.assertEqual(sample[0]['fare'],'200.1234567')

    def test_missing_fields_and_wrong_period_are_rejected(self):
        for key,value in [('fare',None),('year','2025'),('quarter','3')]:
            data=rows();data[0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                business.make_sample(data)

    def test_invalid_numeric_values_are_rejected(self):
        for field,value in [('fare','NaN'),('fare','Infinity'),('fare','-1'),
                            ('fare','text'),('passengers','0'),('large_ms','60')]:
            data=rows();data[0][field]=value
            with self.subTest(field=field,value=value),self.assertRaises(ValueError):
                business.make_sample(data)

    def test_duplicate_and_reversed_pairs_are_rejected(self):
        for reverse in (False,True):
            data=rows();data[1]=copy.deepcopy(data[0])
            if reverse:
                data[1]['citymarketid_1'],data[1]['citymarketid_2']=data[1]['citymarketid_2'],data[1]['citymarketid_1']
            with self.subTest(reverse=reverse),self.assertRaises(ValueError):
                business.make_sample(data)

    def test_bounded_population(self):
        for data in ([],rows()[:29],{},rows()*50):
            with self.assertRaises(ValueError):business.make_sample(data)

    def test_download_replay_separation_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            raw=json.dumps(rows()).encode()
            metadata=json.dumps({'id':business.DATASET_ID,'licenseId':'USGOV_WORKS','attribution':'DOT'}).encode()
            with patch.object(business,'read_public',side_effect=[(raw,'https://example.test/data'),(metadata,'https://example.test/meta')]):
                business.prepare(root/'first')
            with patch.object(business,'read_public',side_effect=AssertionError('Replay must be offline')):
                business.prepare(root/'replay',root/'first')
            for name in ('sample.json','task-inputs.json','answer-key.json','provenance.json'):
                self.assertEqual((root/'first'/name).read_bytes(),(root/'replay'/name).read_bytes())
            tasks=json.loads((root/'first'/'task-inputs.json').read_text())
            self.assertTrue(all('expected' not in task and 'source_dataset' not in task for task in tasks))
            (root/'first'/'raw-rows.json').write_text('[]')
            with self.assertRaises(ValueError):business.prepare(root/'tampered',root/'first')
            with self.assertRaises(FileExistsError):business.prepare(root/'replay')

    def test_license_change_requires_review(self):
        with tempfile.TemporaryDirectory() as directory:
            raw=json.dumps(rows()).encode()
            metadata=json.dumps({'id':business.DATASET_ID,'licenseId':'changed'}).encode()
            with patch.object(business,'read_public',side_effect=[(raw,'url'),(metadata,'url')]):
                with self.assertRaises(ValueError):business.prepare(Path(directory)/'run')


if __name__=='__main__':
    unittest.main()
