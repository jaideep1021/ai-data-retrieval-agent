"""Repair regression tests use synthetic PDFs and mocked API failures."""
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, MagicMock, patch

from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

from autonomous import QueryPlan
from business_agent import BusinessRetriever, BusinessSelection, decimal_value, number_in_quote, evidence_context, run, BatchStop, BudgetExceeded
from business_documents import pdf_text, DocumentError
from evaluate_business import PacedModels
from tests.test_business_agent import TASK


def synthetic_pdf():
    writer = PdfWriter()
    page = writer.add_blank_page(612, 792)
    font = DictionaryObject({NameObject('/Type'): NameObject('/Font'),
                             NameObject('/Subtype'): NameObject('/Type1'),
                             NameObject('/BaseFont'): NameObject('/Helvetica')})
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): font})})
    stream = DecodedStreamObject()
    stream.set_data(b'BT /F1 12 Tf 50 700 Td (Alpha AA   Beta BB   2024 Q4   123.45 USD) Tj ET')
    page[NameObject('/Contents')] = stream
    buf = io.BytesIO(); writer.write(buf)
    return buf.getvalue()


class NumericFormatTests(unittest.TestCase):
    def test_grouped_decimal_preserves_precision(self):
        self.assertEqual(str(decimal_value('3,109')), '3109')
        self.assertEqual(str(decimal_value('1,234,567.8901')), '1234567.8901')
        self.assertTrue(number_in_quote('3,109', 'Passengers 3,109 per day'))
        for malformed in ['1,00', '12,34.5', '1,234,56', 'NaN', '-1,000', '1.234,56']:
            with self.subTest(malformed=malformed), self.assertRaises(ValueError): decimal_value(malformed)


class DocumentTests(unittest.TestCase):
    def test_real_pdf_worker_retains_row(self):
        text = pdf_text(synthetic_pdf())
        self.assertIn('[PDF PAGE 1]', text)
        self.assertIn('123.45', text)
        self.assertIn('Alpha', text)

    def test_bad_pdf_rejected(self):
        with self.assertRaises(DocumentError): pdf_text(b'not a pdf')
        with self.assertRaises(DocumentError): pdf_text(b'%PDF-broken')

    def test_html_rows_and_links(self):
        fetcher = BusinessRetriever(); self.addCleanup(fetcher.session.close)
        html='<main><table><tr><th>Market</th><th>Fare</th></tr><tr><td>Alpha</td><td>123</td></tr></table><a href="/export.csv">Data</a></main>'
        with patch.object(fetcher, 'read', return_value=(200,'text/html',html,'https://example.org')):
            result=fetcher.fetch_document('https://example.org')
        self.assertIn('Alpha | 123',result['text'])
        self.assertEqual(result['links'][0]['url'],'https://example.org/export.csv')

    def test_binary_download_and_redirect_checks(self):
        fetcher=BusinessRetriever(); self.addCleanup(fetcher.session.close)
        response=MagicMock(status_code=200,headers={'Content-Type':'application/pdf'})
        raw=synthetic_pdf(); response.iter_content.return_value=[raw]
        fetcher.session.get=Mock(return_value=MagicMock(__enter__=Mock(return_value=response)))
        with patch('business_agent.public_url',side_effect=lambda url:url), patch.object(fetcher,'check_policy') as policy:
            self.assertEqual(fetcher.read('https://example.org/doc')[2],raw)
            policy.assert_called_once()
        response.status_code=302; response.headers={'Location':'https://127.0.0.1/private'}
        with patch('business_agent.public_url',side_effect=['https://example.org/doc',ValueError('private')]), patch.object(fetcher,'check_policy'):
            with self.assertRaises(ValueError): fetcher.read('https://example.org/doc')

    def test_size_and_robots_limits(self):
        fetcher=BusinessRetriever(); self.addCleanup(fetcher.session.close)
        response=MagicMock(status_code=200,headers={'Content-Type':'application/pdf'})
        response.iter_content.return_value=[b'x'*10_000_001]
        fetcher.session.get=Mock(return_value=MagicMock(__enter__=Mock(return_value=response)))
        with patch('business_agent.public_url',side_effect=lambda url:url), patch.object(fetcher,'check_policy'):
            with self.assertRaises(DocumentError): fetcher.read('https://example.org/doc')
        fetcher.session.get.reset_mock()
        with patch('business_agent.public_url',side_effect=lambda url:url), patch.object(fetcher,'check_policy',side_effect=ValueError('denied')):
            with self.assertRaises(ValueError): fetcher.read('https://example.org/doc')
        fetcher.session.get.assert_not_called()

    def test_pdf_bytes_not_decoded(self):
        fetcher = BusinessRetriever(); self.addCleanup(fetcher.session.close)
        raw = synthetic_pdf()
        with patch.object(fetcher,'read',return_value=(200,'application/pdf',raw,'https://example.org/data.pdf')):
            result=fetcher.fetch_document('https://example.org/data.pdf')
        self.assertEqual(result['raw_bytes'],raw)
        self.assertIn('123.45',result['text'])

    def test_both_markets_preferred_to_early_single_city_rows(self):
        text=('Alpha, AA unrelated\n'+'x'*1500+'\n')*30+'Alpha, AA / Beta, BB TARGET ROW\n'
        context,_=evidence_context(text,TASK)
        self.assertIn('TARGET ROW',context)


class RetryTests(unittest.TestCase):
    @patch('evaluate_business.time.sleep')
    def test_server_retry_preserves_failed_attempt(self,sleep):
        models=Mock(); error=RuntimeError('private'); error.code=503
        response=Mock(usage_metadata=None)
        models.generate_content.side_effect=[error,response]
        wrapper=PacedModels(models)
        self.assertIs(wrapper.generate_content(model='test',config={}),response)
        self.assertEqual([c['status'] for c in wrapper.calls],['error','ok'])
        self.assertEqual(wrapper.calls[0]['retry_wait_seconds'],10)
        self.assertNotIn('private',str(wrapper.calls))

    @patch('evaluate_business.time.sleep')
    def test_quota_not_retried(self,sleep):
        models=Mock(); error=RuntimeError(); error.code=429
        models.generate_content.side_effect=error
        wrapper=PacedModels(models)
        with self.assertRaises(RuntimeError): wrapper.generate_content(model='test',config={})
        self.assertEqual(models.generate_content.call_count,1)

    @patch('evaluate_business.time.sleep')
    def test_retry_limits(self,sleep):
        models=Mock(); error=RuntimeError(); error.code=503
        models.generate_content.side_effect=error
        wrapper=PacedModels(models)
        with self.assertRaises(RuntimeError): wrapper.generate_content(model='test',config={})
        self.assertEqual(len(wrapper.calls),2)
        wrapper.batch_limit=2
        with self.assertRaises(BatchStop): wrapper.generate_content(model='test',config={})
        wrapper.batch_limit=120; wrapper.trial_limit=2
        with self.assertRaises(BudgetExceeded): wrapper.generate_content(model='test',config={})


class QueryTests(unittest.TestCase):
    def test_source_schema_limits_match_runtime(self):
        self.assertEqual(BusinessSelection.model_json_schema()['properties']['candidate_indices']['maxItems'],1)
        with self.assertRaises(ValueError):
            BusinessSelection(candidate_indices=[1,2],reason='too many')

    def test_rejected_proposal_logged_and_repaired(self):
        model=Mock()
        model.ask.side_effect=[QueryPlan(query='site:unknown.example Alpha'),
            QueryPlan(query='Alpha Beta 2024 fare'),QueryPlan(query='Alpha Beta 2024 fare')]
        provider=Mock(); provider.name='brave'; provider.search.return_value=[]
        with tempfile.TemporaryDirectory() as folder:
            result=run(TASK,model,provider,Mock(policy_events=[]),Path(folder)/'run')
        self.assertEqual(result['query_proposals'][0]['status'],'REJECTED')
        self.assertIn('unknown.example',result['query_proposals'][0]['query'])
        self.assertEqual(provider.search.call_count,1)
        self.assertFalse(result['stop_batch'])


if __name__=='__main__': unittest.main()
