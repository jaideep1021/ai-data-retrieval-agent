"""Offline download-inventory failure paths; no network calls."""
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import hashlib
import bts_bulk_download as bulk

class BulkTests(unittest.TestCase):
    def archive(self, root, year='2015', months=(1, 2), duplicate=False):
        path = root / 'response.bin'
        stream = io.StringIO()
        writer = csv.DictWriter(stream, fieldnames=bulk.FIELDS)
        writer.writeheader()
        for month in months:
            row = dict.fromkeys(bulk.FIELDS, '0')
            row.update(YEAR=year, MONTH=str(month), ORIGIN_COUNTRY='US', DEST_COUNTRY='KE', CLASS='F')
            writer.writerow(row)
            if duplicate: writer.writerow(row)
        with zipfile.ZipFile(path, 'w') as z:
            z.writestr('data.csv', stream.getvalue())
        return path

    def test_missing_months_and_duplicate_diagnostics(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.archive(Path(d), duplicate=True)
            report=bulk.inventory(p, 2015)
            self.assertEqual(report['rows'], 4)
            self.assertEqual(report['duplicate_dimension_keys'], 2)
            self.assertEqual(report['missing_months'], list(range(3,13)))
            self.assertFalse(report['source_reporting_completeness_confirmed'])

    def test_wrong_year_and_empty_data(self):
        with tempfile.TemporaryDirectory() as d:
            for options in ({'year':'2016'}, {'months':()}):
                with self.assertRaises(ValueError):
                    bulk.inventory(self.archive(Path(d), **options), 2015)

    def test_bad_archive_and_schema(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'response.bin';p.write_bytes(b'error page')
            with self.assertRaises(zipfile.BadZipFile): bulk.inventory(p,2015)
            with zipfile.ZipFile(p,'w') as z: z.writestr('data.csv','wrong\n1\n')
            with self.assertRaises(ValueError): bulk.inventory(p,2015)

    def test_cache_integrity_and_no_network_on_reuse(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); folder=root/'2015-test';folder.mkdir()
            p=self.archive(folder)
            manifest={'status':'INVENTORIED','year':2015,'fields':bulk.FIELDS,
                      'geography':'All','sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
            (folder/'manifest.json').write_text(json.dumps(manifest))
            with patch.object(bulk,'ROOT',root), patch.object(bulk.urllib.request,'build_opener',side_effect=AssertionError('network')):
                self.assertEqual(bulk.download(2015),(folder,True))
                p.write_bytes(b'changed')
                self.assertIsNone(bulk.cached(2015))
