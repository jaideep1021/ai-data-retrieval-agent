import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from aviation_agent import run, Selection
from business_agent import BusinessRetriever
from business_documents import DocumentError

class OCRScreeningTests(unittest.TestCase):
    def test_opt_in_cap_and_review_labels(self):
        task={'commercial_scope':True,'country':'South Africa','topic':'us_bilateral_air_services'}
        def ocr(source,out):
            out.mkdir();(out/'ocr.txt').write_text('BETWEEN\nTHE GOVERNMENT OF THE REPUBLIC OF SOUTH AFRICA\nAND\nTHE GOVERNMENT OF THE REPUBLIC OF EXAMPLELAND\n')
            return {'status':'OCR_EXTRACTED','text_file':'ocr.txt','partial_coverage':True}
        for enabled in [False,True]:
            with self.subTest(enabled=enabled), tempfile.TemporaryDirectory() as folder:
                reader=BusinessRetriever();self.addCleanup(reader.session.close)
                provider=SimpleNamespace(name='fake',search=lambda q:[{'url':'https://example.org/'+q,'title':'Example agreement title'}])
                with patch.object(reader,'read',return_value=(200,'application/pdf',b'%PDF-fixture','https://example.org')),patch('business_agent.pdf_text',side_effect=DocumentError('PDF_HAS_NO_EXTRACTABLE_TEXT')),patch('optional_pdf_ocr.evaluate_ocr',side_effect=ocr) as mocked:
                    r=run(task,['first','second'],SimpleNamespace(ask=lambda *a:Selection(indices=[0])),provider,reader,Path(folder)/'run',enhanced=True,ocr_screening=enabled)
                self.assertEqual(mocked.call_count,int(enabled))
                self.assertEqual(r['events'],[])
                self.assertTrue(all(d['status']=='READ_FAILED' for d in r['documents']))
                if enabled:
                    review=r['documents'][0]['ocr_screening']
                    self.assertEqual(review['decision'],'PROPOSED_EXCLUSION')
                    self.assertFalse(review['verified'])
                    self.assertIn('DOCUMENT_NOT_FULLY_EXAMINED',review['flags'])
