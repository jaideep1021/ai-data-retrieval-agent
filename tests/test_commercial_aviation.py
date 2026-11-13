"""Synthetic offline checks; examples are not historical agreement evidence."""
import unittest
from commercial_aviation import CommercialEvent, assess_commercial, extract_commercial
from aviation_verification import select_sections
from aviation_agent import Task, make_plan, Plan

class CommercialTests(unittest.TestCase):
    def setUp(self):
        self.task=dict(country='South Africa',topic='us_bilateral_air_services',
            period_start=2009,period_end=2019,commercial_scope=True)
        self.text='South Africa and the United States signed an air services agreement on 1 May 2015. International services are permitted.'
        self.selection=select_sections(self.text,self.task)
        self.ev={'section_id':'S1','quote':self.text}
        self.event=CommercialEvent(country='South Africa',description='Agreement signed',
            topic='bilateral_air_services',document_status='final_instrument',
            evidence=[self.ev],status_evidence=[self.ev],dates=[dict(kind='signed',value='2015-05-01',raw_wording=self.text,evidence=self.ev)],
            international_applicability='explicit',applicability_evidence=[self.ev],notes='',
            event_kind='signature',lifecycle='signed',commercial_claims=[dict(category='parties',statement='South Africa and United States',evidence=self.ev)],
            period_basis='in_window_event',period_evidence=[self.ev],implementation='not_established')
    def audit(self):
        return assess_commercial(self.event,self.selection,self.task,'https://www.state.gov/test')
    def test_signature_does_not_become_effective(self):
        a=self.audit();self.assertIsNone(a['candidate_export_dates']['effective_date'])
        self.assertNotIn('BILATERAL_PARTIES_REQUIRE_REVIEW',a['flags']);self.assertFalse(a['verified'])
    def test_invented_commercial_evidence(self):
        self.event.commercial_claims[0].evidence.quote='Unlimited weekly flights are permitted.'
        self.assertEqual(self.audit()['status'],'UNSUPPORTED')
    def test_metadata_needs_underlying_instrument(self):
        self.event.document_status='metadata'
        self.assertIn('METADATA_NOT_SUBSTANTIVE_EVENT_EVIDENCE',self.audit()['flags'])
    def test_conditional_effect_withheld(self):
        text='South Africa and the United States agreement shall enter into force on 1 May 2015 if notifications are completed.'
        self.selection=select_sections(text,self.task)
        self.event.dates[0].kind='effective';self.event.dates[0].evidence.quote=text
        self.assertIsNone(self.audit()['candidate_export_dates']['effective_date'])
        self.assertIn('CONDITIONAL_OR_NEGATED_EFFECT',self.audit()['date_observations'][0]['issues'])
    def test_assessment_is_not_commercial_consequence(self):
        self.task['topic']='commercial_connectivity_changes'
        self.assertIn('COMMERCIAL_CONSEQUENCE_NOT_ESTABLISHED',self.audit()['flags'])
    def test_missing_parties(self):
        self.event.commercial_claims[0].category='other'
        self.assertIn('BILATERAL_PARTIES_REQUIRE_REVIEW',self.audit()['flags'])
    def test_unknown_period_is_not_invented(self):
        self.event.period_basis='unresolved';self.event.period_evidence=[]
        self.assertIn('PERIOD_APPLICABILITY_REVIEW',self.audit()['flags'])
    def test_extract_uses_commercial_schema_and_review(self):
        event=self.event
        class Model:
            def ask(self,stage,prompt,payload,schema):
                assert stage=='commercial_extract' and 'oversight assessment is not itself a ban' in prompt
                return schema(events=[event])
        r=extract_commercial(self.task,self.text,'https://www.state.gov/test',Model())
        self.assertTrue(r['events'][0]['triage']['human_validation_required'])
        self.assertEqual(r['events'][0]['triage']['decision'],'NEEDS_REVIEW')
    def test_plan_has_no_reference_payload(self):
        task=self.task
        class Model:
            def ask(self,stage,prompt,payload,schema):
                assert payload==task and 'commercial' in prompt
                return Plan(queries=['South Africa United States aviation agreement history','South Africa US air services amendment dates'])
        self.assertEqual(len(make_plan(task,Model())),2)
    def test_live_runner_dispatch_and_search_cap(self):
        import tempfile
        from pathlib import Path
        from types import SimpleNamespace
        from aviation_agent import run, Selection
        event=self.event
        class Model:
            def ask(self,stage,prompt,payload,schema):
                if stage=='select': return Selection(indices=[0])
                assert stage=='commercial_extract'
                return schema(events=[event])
        calls=[]
        def search(q):
            calls.append(q);return [{'url':'https://www.state.gov/test'}]
        def fetch(url, **kwargs):
            return dict(final_url=url,raw_bytes=self.text.encode(),text=self.text,
                raw_sha256='synthetic',content_type='text/plain',links=[])
        with tempfile.TemporaryDirectory() as folder:
            r=run(self.task,['one','two','three'],Model(),SimpleNamespace(name='fake',search=search),
                SimpleNamespace(fetch_document=fetch,policy_events=[]),Path(folder)/'run',enhanced=True)
        self.assertEqual(len(calls),2)
        self.assertEqual(r['usage_counts']['search_requests'],2)
        self.assertEqual(len(r['events']),1)
        self.assertFalse(r['events'][0]['audit']['verified'])
    def test_legacy_path_cannot_bypass_commercial_checks(self):
        import tempfile
        from pathlib import Path
        from aviation_agent import run
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):run(self.task,[],None,None,None,Path(folder)/'run')
    def test_blank_result_does_not_claim_absence(self):
        class Model:
            def ask(self,stage,prompt,payload,schema):return schema(events=[])
        r=extract_commercial(self.task,self.text,'https://www.state.gov/test',Model())
        self.assertEqual(r['empty_result_triage']['decision'],'UNRESOLVED')
    def test_error_page_detector_does_not_reject_regulatory_language(self):
        from commercial_aviation import access_error
        self.assertTrue(access_error('Technical Difficulties Please try again. Exception: forbidden'))
        self.assertFalse(access_error('Unauthorized traffic is forbidden under this agreement.'))
        self.assertFalse(access_error('Technical difficulties may affect services under Article 4.'))
    def test_explicit_heading_mismatch_and_valid_pair(self):
        from commercial_aviation import explicit_counterpart_mismatch
        template='BETWEEN\nTHE GOVERNMENT OF\nTHE REPUBLIC OF SOUTH AFRICA\nAND\nTHE GOVERNMENT OF\n{}\n'
        self.assertIsNotNone(explicit_counterpart_mismatch(template.format('THE REPUBLIC OF EXAMPLELAND'),self.task))
        self.assertIsNone(explicit_counterpart_mismatch(template.format('THE UNITED STATES OF AMERICA'),self.task))
        self.assertIsNone(explicit_counterpart_mismatch('South Africa report mentions Exampleland and the US.',self.task))
    def test_wrapped_prefix_and_memorandum_party_clause(self):
        from commercial_aviation import explicit_counterpart_mismatch as check
        heading='BETWEEN\nTHE GOVERNMENT OF THE\nREPUBLIC OF SOUTH AFRICA\nAND\nTHE GOVERNMENT OF THE\nREPUBLIC OF EXAMPLELAND\n'
        result=check(heading,self.task)
        self.assertEqual(result['parties'],['south africa','exampleland'])
        self.assertIn(result['evidence'],heading)
        memo='EXPLANATORY MEMORANDUM\nThe Government of the Republic of South Africa and the Government of the Republic of\nExampleland have reached consensus on the draft text of the Agreement.'
        result=check(memo,self.task)
        self.assertEqual(result['basis'],'memorandum_party_clause')
        self.assertEqual(result['parties'],['south africa','exampleland'])
        self.assertIn(result['evidence'],memo)
        self.assertIsNone(check(memo.replace('Exampleland','United States of America'),self.task))
        self.assertIsNone(check(memo.replace('have reached consensus','have not reached consensus'),self.task))
        self.assertIsNone(check(memo.replace('EXPLANATORY MEMORANDUM','COMPARISON OF PAST AGREEMENTS'),self.task))
        self.assertIsNone(check(heading+heading.replace('EXAMPLELAND','OTHERLAND'),self.task))
        self.assertIsNone(check('EXPLANATORY MEMORANDUM: South Africa discusses Exampleland and United States agreements.',self.task))
        self.assertIsNone(check(heading,{**self.task,'topic':'aviation_safety_changes'}))

    def test_known_wrong_counterpart_skips_model(self):
        text='BETWEEN\nTHE GOVERNMENT OF\nTHE REPUBLIC OF SOUTH AFRICA\nAND\nTHE GOVERNMENT OF\nTHE REPUBLIC OF EXAMPLELAND\n'
        class Model:
            def ask(self,*args):raise AssertionError('No extraction call should occur')
        result=extract_commercial(self.task,text,'https://example.org',Model())
        self.assertEqual(result['empty_result_triage']['decision'],'OUT_OF_SCOPE')
    def test_garbled_date_preserves_proposal_but_withholds_validated_date(self):
        self.event.dates[0].evidence.quote='Signed on ..?? May two thousand fifteen.'
        a=self.audit()
        self.assertEqual(a['date_observations'][0]['value'],'2015-05-01')
        self.assertIsNone(a['validated_dates'][0]['value'])
        self.assertTrue(a['description_requires_date_review'])
    def test_access_errors_count_attempts_without_extraction(self):
        import tempfile
        from pathlib import Path
        from types import SimpleNamespace
        from aviation_agent import run,Selection
        class Model:
            def ask(self,stage,*args):
                if stage=='select':return Selection(indices=[0])
                raise AssertionError('Error page must not be sent for extraction')
        fetcher=SimpleNamespace(policy_events=[],fetch_document=lambda url, **kwargs:dict(
            text='Technical Difficulties Please try again. Exception: forbidden',
            raw_bytes=b'error',raw_sha256='synthetic',final_url=url,links=[]))
        with tempfile.TemporaryDirectory() as folder:
            r=run(self.task,['one','two'],Model(),SimpleNamespace(name='fake',search=lambda q:[{'url':'https://example.org/'+q}]),fetcher,Path(folder)/'run',enhanced=True)
        self.assertEqual(r['usage_counts']['parent_document_attempts'],2)
        self.assertTrue(all(d['status']=='ACCESS_ERROR' for d in r['documents']))
        self.assertEqual(r['events'],[])
