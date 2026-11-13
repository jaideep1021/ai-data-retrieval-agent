"""Offline tests use synthetic text; they make no network/model calls."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from pydantic import ValidationError
from aviation_agent import Task, Event, Selection, Extraction, audit_event, run


class AviationTests(unittest.TestCase):
    """Guard against fabricated evidence and silent failed-discovery success."""
    def setUp(self):
        self.task = dict(task_id='KEN-safety',country='Kenya',country_iso3='KEN',
            topic='aviation_safety_changes',period_start=2009,period_end=2019,
            include_supported_prior_background=True)
        self.text = 'Kenya oversight assessment was announced on 1 January 2017.'
        self.event = Event(country='Kenya',regulation_type='oversight',
            policy_description='Assessment announced',supporting_evidence=self.text,
            announcement_date='2017-01-01',announcement_quote=self.text,
            effective_date=None,effective_quote=None,date_notes='Effect unknown',
            applicability_notes='Requires review')

    def test_supported_still_needs_human(self):
        self.assertEqual(audit_event(self.event,self.text,self.task)['status'],'NEEDS_HUMAN_REVIEW')
        self.assertFalse(audit_event(self.event,self.text,self.task)['verified'])

    def test_fabricated_quote_rejected(self):
        self.assertEqual(audit_event(self.event,'unrelated text',self.task)['status'],'UNSUPPORTED')

    def test_impossible_date_rejected(self):
        self.event.effective_date='2017-02-30'
        self.event.effective_quote=self.text
        self.assertIn('EFFECTIVE_DATE_INVALID',audit_event(self.event,self.text,self.task)['reasons'])

    def test_date_without_quote_rejected(self):
        self.event.effective_date='2017-01-01'
        self.assertIn('EFFECTIVE_DATE_QUOTE_NOT_FOUND',audit_event(self.event,self.text,self.task)['reasons'])

    def test_reference_input_rejected(self):
        with self.assertRaises(ValidationError):
            Task.model_validate({**self.task,'source_url':'https://example.org'})

    def test_empty_search_is_not_success(self):
        with tempfile.TemporaryDirectory() as folder:
            result=run(self.task,['first','second'],None,
                SimpleNamespace(name='fake',search=lambda q:[]),
                SimpleNamespace(policy_events=[]),Path(folder)/'run')
            self.assertEqual(result['status'],'NO_EVENTS_EXTRACTED')
            self.assertEqual(len(result['searches']),2)

    def test_failed_fetch_saved(self):
        class Reader:
            policy_events=[]
            def fetch_document(self,url, **kwargs):
                raise ValueError('failure')
        model=SimpleNamespace(ask=lambda *a: Selection(indices=[0]))
        with tempfile.TemporaryDirectory() as folder:
            result=run(self.task,['first','second'],model,
                SimpleNamespace(name='fake',search=lambda q:[{'url':'https://example.org'}]),
                Reader(),Path(folder)/'run')
            self.assertEqual(result['documents'][0]['status'],'FETCH_FAILED')
            self.assertEqual(result['events'],[])

    def test_parent_parse_failure_preserves_bytes_and_recovery(self):
        import hashlib
        from unittest.mock import patch
        from business_agent import BusinessRetriever
        from business_documents import DocumentError
        from staged_retrieval import recovery_query
        raw = b'%PDF-synthetic-unreadable'
        reader = BusinessRetriever()
        self.addCleanup(reader.session.close)
        source = {'url':'https://example.org/scan.pdf', 'title':'Bilateral air services agreement'}
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'run'
            with patch.object(reader, 'read', return_value=(200,'application/pdf',raw,source['url'])), patch('business_agent.pdf_text', side_effect=DocumentError('PDF_HAS_NO_EXTRACTABLE_TEXT')):
                result = run(self.task,['first'],SimpleNamespace(ask=lambda *a:Selection(indices=[0])),
                             SimpleNamespace(name='fake',search=lambda q:[source]),reader,output)
            d = result['documents'][0]
            self.assertEqual(d['status'],'READ_FAILED')
            self.assertEqual(d['reason'],'PDF_HAS_NO_EXTRACTABLE_TEXT')
            self.assertEqual((output/d['raw_file']).read_bytes(),raw)
            self.assertEqual(d['raw_sha256'],hashlib.sha256(raw).hexdigest())
            self.assertEqual(d['bytes'],len(raw))
            self.assertFalse((output/'document-1.txt').exists())
            self.assertEqual(result['events'],[])
            self.assertIsNotNone(recovery_query(self.task,[d]))
            saved = __import__('json').loads((output/'result.json').read_text())
            self.assertEqual(saved['documents'][0]['raw_file'],d['raw_file'])

    def test_download_failure_does_not_preserve_stale_response(self):
        from unittest.mock import patch
        from business_agent import BusinessRetriever
        reader = BusinessRetriever()
        self.addCleanup(reader.session.close)
        reader.response_bytes = b'previous response'
        with tempfile.TemporaryDirectory() as folder, patch.object(reader,'read',side_effect=ValueError('denied')):
            output = Path(folder)/'run'
            result=run(self.task,['first'],SimpleNamespace(ask=lambda *a:Selection(indices=[0])),
                SimpleNamespace(name='fake',search=lambda q:[{'url':'https://example.org'}]),reader,output)
            self.assertEqual(result['documents'][0]['status'],'FETCH_FAILED')
            self.assertNotIn('raw_file',result['documents'][0])
            self.assertEqual(list(output.glob('*.bin')),[])

    def test_nested_wire_schema_and_local_strictness(self):
        import json
        self.assertNotIn('additionalProperties', json.dumps(Extraction.model_json_schema()))
        with self.assertRaises(ValidationError):
            Extraction.model_validate({'events': [{**self.event.model_dump(), 'invented': True}]})

    def test_autonomous_result_preserves_evidence_and_unknown_date(self):
        event, text = self.event, self.text
        class Model:
            def ask(self, stage, *args):
                return Selection(indices=[0]) if stage == 'select' else Extraction(events=[event])
        class Reader:
            policy_events=[]
            def fetch_document(self, url, **kwargs):
                return dict(raw_bytes=text.encode(),text=text,links=[],final_url=url,
                            raw_sha256='fixture')
        with tempfile.TemporaryDirectory() as folder:
            result=run(self.task,['first'],Model(),
                SimpleNamespace(name='fake',search=lambda q:[{'url':'https://example.org'}]),
                Reader(),Path(folder)/'run')
            self.assertEqual(result['status'],'CANDIDATES_FOR_REVIEW')
            self.assertIsNone(result['events'][0]['effective_date'])
            self.assertFalse(result['events'][0]['audit']['verified'])
            self.assertTrue((Path(folder)/'run/document-1.txt').exists())

    def test_invented_selection_cannot_fetch(self):
        with tempfile.TemporaryDirectory() as folder:
            result=run(self.task,['first'],SimpleNamespace(ask=lambda *a:Selection(indices=[99])),
                SimpleNamespace(name='fake',search=lambda q:[{'url':'https://example.org'}]),
                SimpleNamespace(policy_events=[]),Path(folder)/'run')
            self.assertEqual(result['status'],'ERROR')
            self.assertEqual(result['documents'],[])
