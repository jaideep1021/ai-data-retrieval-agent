"""Experimental accept/review/unresolved routing, with no automatic publication.

Rules are deliberately conservative and uncalibrated. WOULD_ACCEPT is a shadow
recommendation, never a verified result. Keep human labels separate for evaluation.
"""
import re
from autonomous import normalized

VERSION = 'aviation-triage-shadow-v1'


def route_event(event, audit, selection, task):
    """Route one already-audited candidate without altering any extracted fields.

    A failed grounding/country/topic check cannot be accepted as written. Other
    ambiguities get targeted review questions. Automatic acceptance is simulated
    only for fully examined, explicitly dated final instruments on registered
    primary-source hosts. These heuristics must be evaluated against human labels.
    No cross-document independence or global absence of contradictions is assumed.
    """
    flags = set(audit.get('flags', []))
    base = {'policy_version': VERSION, 'mode': 'SHADOW', 'verified': False,
            'acceptance_applied': False, 'human_validation_required': True}
    blocking = flags & {'UNGROUNDED_EVIDENCE','COUNTRY_MISMATCH','TOPIC_MISMATCH'}
    if audit.get('status') == 'UNSUPPORTED' or blocking:
        return {**base, 'decision':'UNRESOLVED', 'reasons':sorted(blocking or {'UNSUPPORTED_EVIDENCE'}),
                'review_questions':['Can new or corrected evidence support this claim? Do not accept it as written.']}
    reasons = set(flags)
    if not selection.get('all_sections_selected', False):
        reasons.add('DOCUMENT_NOT_FULLY_EXAMINED')
    if event.document_status != 'final_instrument':
        reasons.add('FINAL_INSTRUMENT_NOT_ESTABLISHED')
    role = audit.get('source_assessment',{}).get('role')
    if role not in {'aviation_regulator','legal_publication_service','foreign_affairs_publisher','foreign_affairs_archive'}:
        reasons.add('COMPETENT_PRIMARY_SOURCE_NOT_ESTABLISHED')
    expected = {'aviation_safety_changes':'safety_oversight',
                'us_bilateral_air_services':'bilateral_air_services'}.get(task['topic'])
    if expected is None or event.topic != expected:
        reasons.add('TOPIC_SCOPE_REVIEW')
    # Date absence is not a false claim, but requires review of historical scope.
    dates = audit.get('date_observations',[])
    usable = [d for d in dates if d['kind'] in ('announced','effective') and d.get('value') and not d.get('issues')]
    if not any(task['period_start']<=int(d['value'][:4])<=task['period_end'] for d in usable):
        reasons.add('EVENT_DATE_IN_WINDOW_NOT_ESTABLISHED')
    country_text = ' '.join(normalized(e.quote) for e in event.evidence)
    if normalized(task['country']) not in country_text:
        reasons.add('COUNTRY_NOT_EXPLICIT_IN_EVENT_EVIDENCE')
    status_text = ' '.join(normalized(e.quote) for e in event.status_evidence)
    # Conventional drafting boilerplate ("makes the following regulations") is
    # deliberately insufficient, because it also occurs in unsigned drafts.
    if not re.search(r'\b(has entered into force|entered into force|came into force|hereby enacted|was enacted)\b', status_text):
        reasons.add('POSITIVE_ENACTMENT_EVIDENCE_REQUIRED')
    all_text = ' '.join(normalized(s['text']) for s in selection.get('sections',[]))
    if re.search(r'\b(draft|proposed|not yet|shall enter|will enter|subject to ratification)\b',all_text):
        reasons.add('PROVISIONAL_OR_CONDITIONAL_LANGUAGE')
    # Reject simple negated enactment wording; this is not a general entailment model.
    if re.search(r'\b(not|never)\b.{0,70}\b(force|enacted)\b',status_text):
        reasons.add('NEGATED_ENACTMENT_LANGUAGE')
    applicability = ' '.join(normalized(e.quote) for e in event.applicability_evidence)
    if event.international_applicability != 'explicit' or not re.search(r'\b(international|foreign aircraft|other states)\b',applicability):
        reasons.add('INTERNATIONAL_APPLICABILITY_UNESTABLISHED')
    if reasons:
        questions=[]
        groups=[
            ({'DOCUMENT_NOT_FULLY_EXAMINED'},'Check omitted sections for commencement, signature and contradictory provisions.'),
            ({'FINAL_INSTRUMENT_NOT_ESTABLISHED','POSITIVE_ENACTMENT_EVIDENCE_REQUIRED','NOT_ESTABLISHED_AS_ENACTED','INCOMPLETE_DATING_LINE','PROVISIONAL_OR_CONDITIONAL_LANGUAGE','NEGATED_ENACTMENT_LANGUAGE'},'Is this a final instrument or a draft/conditional proposal? Locate final-status evidence.'),
            ({'UNDERLYING_INSTRUMENT_REQUIRED','COMPETENT_PRIMARY_SOURCE_NOT_ESTABLISHED','AUTHORITY_UNCLASSIFIED'},'Find the underlying instrument and confirm the publisher is competent for this claim.'),
            ({'DATE_REVIEW_REQUIRED','EVENT_DATE_IN_WINDOW_NOT_ESTABLISHED','DATES_OUTSIDE_WINDOW_CHECK_BACKGROUND','CONFLICTING_EFFECTIVE_DATES','CONFLICTING_ANNOUNCED_DATES'},'What does each date mean, and does it establish an event in 2009–2019 or supported earlier background?'),
            ({'TOPIC_SCOPE_REVIEW','INTERNATIONAL_APPLICABILITY_UNESTABLISHED','COUNTRY_NOT_EXPLICIT_IN_EVENT_EVIDENCE'},'Does the evidence support the country, requested topic and international applicability?')]
        for keys,question in groups:
            if reasons & keys:
                questions.append(question)
        if not questions:
            questions=['Resolve the listed evidence flags before accepting the event.']
        return {**base,'decision':'NEEDS_REVIEW','reasons':sorted(reasons),'review_questions':questions}
    return {**base,'decision':'WOULD_ACCEPT','reasons':['ALL_SHADOW_GATES_PASSED'],
            'review_questions':['Validate this proposed automatic acceptance against the full source; record any missed error.']}


def route_empty():
    """An empty extraction is unresolved retrieval, never evidence of no regulation."""
    return {'policy_version':VERSION,'mode':'SHADOW','decision':'UNRESOLVED',
            'verified':False,'acceptance_applied':False,'human_validation_required':True,
            'reasons':['NO_CANDIDATE'],'review_questions':['Is more retrieval needed? No candidate does not prove no event exists.']}
