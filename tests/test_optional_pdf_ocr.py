"""Offline safety-path tests; no OCR engine or network needed."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from optional_pdf_ocr import evaluate_ocr

class OptionalOCRTests(unittest.TestCase):
    def test_missing_engine_preserves_source_and_labels_unavailable(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'scan.pdf';source.write_bytes(b'%PDF-fixture')
            with patch('optional_pdf_ocr.shutil.which',return_value=None):
                r=evaluate_ocr(source,Path(d)/'out')
            self.assertEqual(r['status'],'UNAVAILABLE')
            self.assertEqual(r['pages_ocrd'],[])
            self.assertTrue(r['requires_visual_review'])
            self.assertEqual(source.read_bytes(),b'%PDF-fixture')
            self.assertEqual(json.loads((Path(d)/'out/ocr-manifest.json').read_text()),r)
    def test_timeout_is_recorded_without_claiming_text(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'scan.pdf';source.write_bytes(b'%PDF-fixture')
            with patch('optional_pdf_ocr.shutil.which',return_value='/fake'),patch('optional_pdf_ocr.subprocess.run',side_effect=subprocess.TimeoutExpired('ocr',30)):
                r=evaluate_ocr(source,Path(d)/'out')
            self.assertEqual(r['reason'],'OCR_TIMEOUT')
            self.assertEqual(r['status'],'OCR_FAILED')
            self.assertNotIn('text_file',r)
    def test_invalid_page_budget_rejected(self):
        for n in [0,4,True]:
            with self.assertRaises(ValueError):evaluate_ocr('unused','unused',n)
