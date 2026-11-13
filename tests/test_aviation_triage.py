"""Synthetic routing tests test rules, not empirical acceptance accuracy."""
import unittest
from aviation_verification import RegulatoryEvent, Evidence, DateObservation, select_sections, assess
from aviation_triage import route_event, route_empty


class TriageTests(unittest.TestCase):
    """All decisions remain shadow recommendations, including positive fixtures."""
    def setUp(self):
        self.task={'country':'Kenya','topic':'aviation_safety_changes','period_start':2009,'period_end':2019}
        self.text='Kenya international aviation safety rules entered into force on 4 May 2018.'
        self.selection=select_sections(self.text,self.task)
        quote=Evidence(section_id='S1',quote=self.text)
        self.event=RegulatoryEvent(country='Kenya',description='Safety rules commenced',topic='safety_oversight',
          document_status='final_instrument',evidence=[quote],status_evidence=[quote],
          dates=[DateObservation(kind='effective',value='2018-05-04',raw_wording='4 May 2018',evidence=quote)],
          international_applicability='explicit',applicability_evidence=[quote],notes='Synthetic fixture')

    def decision(self):
        """Exercise the actual verifier and router together, not a hand-built audit."""
        audit=assess(self.event,self.selection,self.task,'https://kcaa.or.ke/test')
        return route_event(self.event,audit,self.selection,self.task)

    def test_clear_fixture_would_accept_but_not_verify(self):
        result=self.decision()
        self.assertEqual(result['decision'],'WOULD_ACCEPT')
        self.assertFalse(result['verified'])
        self.assertFalse(result['acceptance_applied'])
        self.assertTrue(result['human_validation_required'])

    def test_fabricated_quote_unresolved(self):
        self.event.evidence=[Evidence(section_id='S1',quote='This sentence does not exist.')]
        self.assertEqual(self.decision()['decision'],'UNRESOLVED')

    def test_incomplete_coverage_review(self):
        self.selection['all_sections_selected']=False
        self.assertEqual(self.decision()['decision'],'NEEDS_REVIEW')

    def test_unknown_date_review(self):
        self.event.dates=[]
        self.assertIn('EVENT_DATE_IN_WINDOW_NOT_ESTABLISHED',self.decision()['reasons'])

    def test_draft_review(self):
        self.event.document_status='draft'
        self.assertEqual(self.decision()['decision'],'NEEDS_REVIEW')

    def test_conditional_and_negated_text_review(self):
        self.selection=select_sections(self.text+' These are proposed rules.',self.task)
        self.assertIn('PROVISIONAL_OR_CONDITIONAL_LANGUAGE',self.decision()['reasons'])
        text='Kenya international rules have not entered into force on 4 May 2018.'
        self.selection=select_sections(text,self.task)
        quote=Evidence(section_id='S1',quote=text)
        self.event.evidence=[quote];self.event.status_evidence=[quote]
        self.event.applicability_evidence=[quote];self.event.dates[0].evidence=quote
        self.assertIn('NEGATED_ENACTMENT_LANGUAGE',self.decision()['reasons'])

    def test_empty_not_negative_fact(self):
        self.assertEqual(route_empty()['decision'],'UNRESOLVED')
        self.assertFalse(route_empty()['verified'])
