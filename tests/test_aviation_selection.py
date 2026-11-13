"""Synthetic integration checks for budgets, deferred leads and auditability."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from aviation_agent import run
from aviation_selection import ExplainedSelection,validate_assessments

class SelectionTests(unittest.TestCase):
    def test_duplicate_and_missing_assessments_rejected(self):
        for assessments in [[],[{'index':0,'role':'uncertain','reason':'x'}]*2]:
            with self.assertRaises(ValueError):
                validate_assessments(ExplainedSelection(indices=[],assessments=assessments),2)
    def test_invalid_selected_index_rejected(self):
        with self.assertRaises(ValueError):validate_assessments(ExplainedSelection(indices=[2],assessments=[{'index':0,'role':'instrument','reason':'x'}]),1)
    def test_deferred_navigation_survives_empty_second_search(self):
        task={'commercial_scope':True,'topic':'us_bilateral_air_services','country':'South Africa','period_start':2009,'period_end':2019}
        urls=['https://archive.example/a','https://archive.example/b','https://other.example/directory']
        searches=[];payloads=[];fetched=[]
        def search(q):
            searches.append(q)
            return [{'url':u,'title':'Observed air services agreement directory','snippet':''} for u in urls] if len(searches)==1 else []
        class Model:
            def ask(self,stage,prompt,payload,schema):
                if stage=='select':
                    payloads.append(payload)
                    return schema(indices=list(range(len(payload['candidates']))),assessments=[{'index':i,'role':'official_navigation','reason':'Observed official directory lead'} for i in range(len(payload['candidates']))])
                return schema(events=[])
        def fetch(url, **kwargs):
            fetched.append(url)
            text='Technical Difficulties Please try again. Exception: forbidden' if 'archive.' in url else 'Directory of air services agreements. No substantive provisions on this page.'
            return {'final_url':url,'text':text,'raw_bytes':text.encode(),'raw_sha256':'synthetic','content_type':'text/plain','links':[]}
        with tempfile.TemporaryDirectory() as folder:
            r=run(task,['first','second'],Model(),SimpleNamespace(name='fake',search=search),SimpleNamespace(policy_events=[],fetch_document=fetch),Path(folder)/'run',enhanced=True)
        self.assertEqual(fetched,urls)
        self.assertEqual(len(searches),2)
        self.assertEqual(len(payloads[1]['access_history']),2)
        self.assertEqual(payloads[1]['deferred_urls'],[urls[2]])
        self.assertEqual(payloads[1]['candidates'][0]['url'],urls[2])
        self.assertEqual(r['searches'][0]['candidate_dispositions'][2]['status'],'deferred')
        self.assertEqual(r['searches'][1]['candidate_dispositions'][0]['status'],'attempted')
        self.assertEqual(r['usage_counts']['parent_document_attempts'],3)
        self.assertEqual(r['events'],[])
    def test_no_selection_reasons_are_saved(self):
        task={'commercial_scope':True,'topic':'us_bilateral_air_services','country':'South Africa'}
        class Model:
            def ask(self,stage,prompt,payload,schema):
                return schema(indices=[],assessments=[{'index':0,'role':'unrelated','reason':'Explicit other counterpart'}])
        with tempfile.TemporaryDirectory() as folder:
            r=run(task,['first'],Model(),SimpleNamespace(name='fake',search=lambda q:[{'url':'https://example.org'}]),SimpleNamespace(policy_events=[]),Path(folder)/'run',enhanced=True)
        self.assertEqual(r['searches'][0]['selection_output']['assessments'][0]['role'],'unrelated')
        self.assertEqual(r['documents'],[])
    def test_safe_access_codes_preserve_policy_failure_without_raw_errors(self):
        from aviation_selection import safe_access_reason
        self.assertEqual(safe_access_reason(ValueError('Robots policy unavailable or access denied')),'ROBOTS_UNAVAILABLE_OR_DENIED')
        self.assertEqual(safe_access_reason(ValueError('Robots disallows retrieval')),'ROBOTS_DISALLOWED')
        self.assertEqual(safe_access_reason(ValueError('private arbitrary exception detail')),'RETRIEVAL_FAILED')
        self.assertEqual(safe_access_reason(SimpleNamespace(reason_code='SOURCE_HTTP_503')),'SOURCE_HTTP_503')
