"""Synthetic failure-path tests: no credential or network access."""
import json
import unittest
from aviation_verification import (Evidence, DateObservation, RegulatoryEvent,
    RegulatoryExtraction, select_sections, assess, source_role, date_in_wording)


class VerificationTests(unittest.TestCase):
    """Test false date/status confidence, citation boundaries and full-text coverage."""
    def setUp(self):
        self.task={'country':'Kenya','topic':'aviation_safety_changes','period_start':2009,'period_end':2019}
        self.text='Kenya regulations. dc.date.issued | 2018-05-04'
        self.selection=select_sections(self.text,self.task)
        self.evidence=Evidence(section_id='S1',quote=self.text)
        self.event=RegulatoryEvent(country='Kenya',description='Regulatory document',topic='safety_oversight',
            document_status='metadata',evidence=[self.evidence],status_evidence=[self.evidence],dates=[],
            international_applicability='not_shown',applicability_evidence=[],notes='')

    def audit(self):
        """Use the repository host so tests exercise claim-specific source roles."""
        return assess(self.event,self.selection,self.task,'https://libraryir.parliament.go.ke/item')

    def test_metadata_cannot_be_announcement(self):
        self.event.dates=[DateObservation(kind='announced',value='2018-05-04',raw_wording=self.text,evidence=self.evidence)]
        result=self.audit()
        self.assertIsNone(result['candidate_export_dates']['announcement_date'])
        self.assertIn('DATE_REVIEW_REQUIRED',result['flags'])

    def test_issued_date_retained_without_export(self):
        self.event.dates=[DateObservation(kind='issued',value='2018-05-04',raw_wording=self.text,evidence=self.evidence)]
        result=self.audit()
        self.assertEqual(result['date_observations'][0]['issues'],[])
        self.assertIsNone(result['candidate_export_dates']['effective_date'])
        self.assertFalse(result['verified'])

    def test_fake_section_and_spliced_quote_fail(self):
        self.event.evidence=[Evidence(section_id='S999',quote=self.text)]
        self.assertEqual(self.audit()['status'],'UNSUPPORTED')
        self.event.evidence=[Evidence(section_id='S1',quote='Kenya ... 2018-05-04')]
        self.assertEqual(self.audit()['status'],'UNSUPPORTED')

    def test_separate_real_quotes_allowed(self):
        self.event.evidence=[Evidence(section_id='S1',quote='Kenya regulations.'),
                             Evidence(section_id='S1',quote='dc.date.issued | 2018-05-04')]
        self.assertNotIn('UNGROUNDED_EVIDENCE',self.audit()['flags'])

    def test_full_document_selection_includes_tail(self):
        text=''.join(f'[PDF PAGE {n}]\n'+('ordinary content '*180)+'\n' for n in range(1,97))
        text+='Dated the ………………………2020.'
        selected=select_sections(text,self.task)
        prefix=select_sections(text,self.task,mode='prefix')
        self.assertIn(96,selected['selected_pages'])
        self.assertNotIn(96,prefix['selected_pages'])
        self.assertLessEqual(selected['selected_characters'],24000)
        self.assertFalse(selected['all_sections_selected'])
        for section in selected['sections']:
            self.assertEqual(text[section['start']:section['end']],section['text'])

    def test_unknown_and_lookalike_hosts(self):
        self.assertEqual(source_role('https://kcaa.or.ke.evil.example')['role'],'unclassified')
        self.assertEqual(source_role('https://kcaa.or.ke')['role'],'aviation_regulator')

    def test_date_lexical_checks(self):
        self.assertTrue(date_in_wording('2018-05-04','Issued 4 May 2018'))
        self.assertFalse(date_in_wording('2018-05-04','Issued 5 April 2018'))
        self.assertFalse(date_in_wording('2018-02-30','Issued 2018-02-30'))
        self.assertFalse(date_in_wording('2018-05-04','Issued May 2018'))

    def test_draft_not_accepted(self):
        self.event.document_status='draft'
        self.assertIn('NOT_ESTABLISHED_AS_ENACTED',self.audit()['flags'])
        self.assertFalse(self.audit()['verified'])

    def test_schema_has_no_unsupported_nested_keywords(self):
        self.assertNotIn('additionalProperties',json.dumps(RegulatoryExtraction.model_json_schema()))

    def test_conflicting_effective_dates_not_exported(self):
        text='Effective 4 May 2018. Effective 5 May 2018.'
        self.selection=select_sections(text,self.task)
        self.event.evidence=[Evidence(section_id='S1',quote=text)]
        self.event.status_evidence=[]
        self.event.dates=[DateObservation(kind='effective',value=f'2018-05-0{n}',
            raw_wording=f'{n} May 2018',evidence=Evidence(section_id='S1',quote=f'Effective {n} May 2018.')) for n in [4,5]]
        result=self.audit()
        self.assertIsNone(result['candidate_export_dates']['effective_date'])
        self.assertIn('CONFLICTING_EFFECTIVE_DATES',result['flags'])

    def test_blank_dated_line_overrides_final_label(self):
        self.selection=select_sections('Kenya instrument. Dated the ………………………2020.',self.task)
        self.event.document_status='final_instrument'
        self.assertIn('INCOMPLETE_DATING_LINE',self.audit()['flags'])

    def test_prefix_budget_counts_no_overlap_twice(self):
        selection=select_sections('abc '*10000,self.task,mode='prefix')
        self.assertLessEqual(selection['selected_characters'],24000)

    def test_live_enhanced_path_uses_same_verifier(self):
        import tempfile
        from pathlib import Path
        from types import SimpleNamespace
        from aviation_agent import run, Selection
        event,text=self.event,self.text
        class Model:
            def ask(self,stage,*args):
                return Selection(indices=[0]) if stage=='select' else RegulatoryExtraction(events=[event])
        reader=SimpleNamespace(policy_events=[],fetch_document=lambda url, **kwargs:dict(
            text=text,raw_bytes=text.encode(),raw_sha256='fixture',final_url=url,links=[]))
        provider=SimpleNamespace(name='fake',search=lambda q:[{'url':'https://libraryir.parliament.go.ke/item'}])
        with tempfile.TemporaryDirectory() as folder:
            result=run(self.task,['query'],Model(),provider,reader,Path(folder)/'run',enhanced=True)
            self.assertEqual(result['status'],'CANDIDATES_FOR_REVIEW')
            self.assertIn('UNDERLYING_INSTRUMENT_REQUIRED',result['events'][0]['audit']['flags'])
            self.assertTrue((Path(folder)/'run/document-1-review.json').exists())
