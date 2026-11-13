"""Offline synthetic recovery tests with no actual agreement answers."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from aviation_agent import run, Selection
from staged_retrieval import recovery_query

class StagedTests(unittest.TestCase):
    def setUp(self):
        self.task={'commercial_scope':True,'country':'South Africa','topic':'us_bilateral_air_services'}
    def test_query_comes_from_observed_title(self):
        d={'url':'https://example.org/a','title':'Example Agreement 123','status':'ACCESS_ERROR'}
        q=recovery_query(self.task,[d])
        self.assertIn('Example Agreement 123',q['query'])
        self.assertEqual(q['source_url'],d['url'])
    def test_missing_title_and_readable_source_do_not_trigger_recovery(self):
        self.assertIsNone(recovery_query(self.task,[{'url':'x','title':'','status':'FETCH_FAILED'}]))
        self.assertIsNone(recovery_query(self.task,[{'url':'x','title':'Example agreement title','status':'READ'}]))
    def test_operators_and_urls_removed(self):
        q=recovery_query(self.task,[{'url':'x','title':'Example agreement title site:bad.org https://bad.org','status':'ACCESS_ERROR'}])
        self.assertNotIn('bad.org',q['query']);self.assertLessEqual(len(q['query']),240)
    def test_three_first_results_do_not_exhaust_second_search(self):
        calls=[]
        def search(q):
            calls.append(q)
            return [{'url':f'https://example.org/{len(calls)}/{i}','title':f'Example Agreement {i}'} for i in range(3)]
        class Model:
            def ask(self,stage,*args):
                assert stage=='select'
                return Selection(indices=[0,1,2])
        reader=SimpleNamespace(policy_events=[],fetch_document=lambda url, **kwargs:dict(final_url=url,raw_bytes=b'error',raw_sha256='synthetic',text='Technical Difficulties Please try again. Exception: forbidden',links=[]))
        with tempfile.TemporaryDirectory() as folder:
            r=run(self.task,['first','second'],Model(),SimpleNamespace(name='fake',search=search),reader,Path(folder)/'run',enhanced=True)
        self.assertEqual(len(calls),2)
        self.assertEqual(r['usage_counts']['parent_document_attempts'],3)
        self.assertEqual(r['searches'][1]['purpose'],'access_recovery')
        self.assertEqual(r['searches'][1]['planned_query'],'second')
        self.assertIn('Example Agreement 0',calls[1])

        # Assert the intended failure, not merely that some exception triggered recovery.
        self.assertTrue(all(d['status']=='ACCESS_ERROR' for d in r['documents']))
        self.assertTrue(all(d['reason']=='SERVICE_ERROR_PAGE' for d in r['documents']))

    def test_commercial_read_failure_preserves_and_triggers_second_search(self):
        import hashlib
        from unittest.mock import patch
        from business_agent import BusinessRetriever
        from business_documents import DocumentError
        raw = b'%PDF-synthetic-scan'
        calls, stages = [], []
        source = {'url':'https://example.org/scan.pdf','title':'Example bilateral agreement'}
        def search(query):
            calls.append(query)
            return [source] if len(calls)==1 else []
        class Model:
            def ask(self,stage,*args):
                stages.append(stage)
                return Selection(indices=[0])
        reader = BusinessRetriever()
        self.addCleanup(reader.session.close)
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'run'
            with patch.object(reader,'read',return_value=(200,'application/pdf',raw,source['url'])), patch('business_agent.pdf_text',side_effect=DocumentError('PDF_HAS_NO_EXTRACTABLE_TEXT')):
                result=run(self.task,['first','second'],Model(),SimpleNamespace(name='fake',search=search),reader,output,enhanced=True)
            document=result['documents'][0]
            self.assertEqual(document['status'],'READ_FAILED')
            self.assertEqual(document['reason'],'PDF_HAS_NO_EXTRACTABLE_TEXT')
            self.assertEqual((output/document['raw_file']).read_bytes(),raw)
            self.assertEqual(document['raw_sha256'],hashlib.sha256(raw).hexdigest())
            self.assertEqual(result['searches'][1]['purpose'],'access_recovery')
            self.assertEqual(result['searches'][1]['recovery_basis']['reason'],'PDF_HAS_NO_EXTRACTABLE_TEXT')
            self.assertIn('Example bilateral agreement',calls[1])
            self.assertEqual(len(calls),2)
            self.assertEqual(result['usage_counts']['parent_document_attempts'],1)
            self.assertEqual(result['events'],[])
            self.assertTrue(all(stage=='select' for stage in stages))
