"""Prepare the focused review queue from downloaded PDF evidence.

This development packaging step provides researcher-authored questions. Questions
are not automatic corrections, reference answers or independent human labels.
"""
import hashlib
import json
from pathlib import Path


def snippets(result, refs):
    """Show exact machine-cited passages with readable page references."""
    sections={s['section_id']:s for s in result['selection']['sections']}
    return '\n\n'.join(f"Page {sections.get(e['section_id'],{}).get('page','?')}: {e['quote']}" for e in refs)


def item(ident,question,current,why,evidence,where,example):
    """Use a consistent, plain-language review-card structure."""
    return dict(id=ident,question=question,current=current,why=why,evidence=evidence,where=where,example=example)


def build():
    """Package three current documents without changing the machine proposals."""
    output=Path('runs/aviation-final-review-20261110');output.mkdir(exist_ok=True)
    task=json.loads(Path('runs/aviation-shadow-policy-20261109/decisions.json').read_text())['task']
    from aviation_verification import RegulatoryEvent,assess
    from aviation_triage import route_event
    cards=[]
    for ident,title,result_path,pdf in [
        ('brave-1-sections-1','1. Security regulations',Path('runs/aviation-verification-20261109/brave-1-sections.json'),Path('runs/aviation-demo-20261109-schema-fix/brave/document-1.bin')),
        ('serpapi-1-sections-1','2. Safety-management regulations',Path('runs/aviation-attachment-fallback-20261110/extraction/candidate-1.json'),Path('runs/aviation-attachment-fallback-20261110/candidate-1/attachment-1.pdf')),
        ('serpapi-2-sections-1','3. Unmanned-aircraft regulations',Path('runs/aviation-attachment-fallback-20261110/extraction/candidate-2.json'),Path('runs/aviation-attachment-fallback-20261110/candidate-2/attachment-1.pdf'))]:
        result=json.loads(result_path.read_text());e=result['events'][0]
        event=RegulatoryEvent.model_validate({k:e[k] for k in RegulatoryEvent.model_fields})
        audit=assess(event,result['selection'],task,e['source_url'])
        route=route_event(event,audit,result['selection'],task)['decision']
        if ident.startswith('brave'):
            items=[item('status','Can this be treated as a final, enacted regulation?',e['document_status'],
                'The final dating line is incomplete. A document title does not prove enactment.',snippets(result,e['status_evidence']),
                'Saved PDF page 96; opening provisions. A final gazette record may be needed.',
                'If final status cannot be established: choose “Still unknown” and write “Need the final gazetted instrument; do not label enacted.”'),
                item('dates','Should announcement and effective dates remain unknown?','Both unknown',
                'The title says 2019; the incomplete dating line ends in 2020. Neither supplies a full effective date.',snippets(result,[d['evidence'] for d in e['dates']]),
                'PDF page 96 and any commencement/publication evidence.',
                'Choose “Keep” if unknown is appropriate. Do not enter January 1 merely because a year appears.'),
                item('scope','Does this security document belong in our connectivity study?',e['topic'],
                'Security provisions are not automatically safety restrictions or evidence of an actual connectivity change.',snippets(result,e['applicability_evidence']),
                'PDF pages 5–6, application and purpose. Read the surrounding provisions.',
                'If you cannot decide study relevance: choose “Still unknown” and ask to confirm whether aviation security is within scope.')]
        elif 'serpapi-1' in ident:
            items=[item('description','Which earlier regulations does this document revoke?',e['description'],
                'The generated description says “2018/2015 regulations”; the cited revocation text identifies 2015. Check and correct that wording.',snippets(result,e['evidence']),
                'Downloaded PDF regulation 18; use the quoted passage and its surrounding text.',
                'If regulation 18 confirms it, choose “Correct”, specify “revokes the 2015 regulations”, and cite the page plus exact passage.'),
                item('dates','Which date meanings are actually supported?', '; '.join(f"{d['kind']}: {d['value']}" for d in e['dates'])+'; announcement/effect unknown',
                'The PDF gives a Gazette date and a separate “Dated” line. Do not turn either automatically into commencement or announcement.',snippets(result,[d['evidence'] for d in e['dates']]),
                'PDF page 1 (Gazette header) and page 20 (dated line); look for commencement provisions if needed.',
                'Keep publication separately. If “signed” is too strong, correct it to “document dated 26 March 2018”, citing page 20. Leave effect unknown unless established.'),
                item('scope','What provision connects these rules to our international aviation question?',e['international_applicability'],
                'Reference to an international convention alone may not establish applicability to the operations in our study.',snippets(result,e['applicability_evidence']),
                'Application provision (regulation 3) and relevant operations provisions in the full downloaded PDF.',
                'If the cited passage is insufficient: choose “Still unknown” and state which application provision or evidence is missing.')]
        else:
            items=[item('status','Is this a draft or a final regulation?',e['document_status'],
                'The official download filename says Draft. The model relied on the title to call it final; final status is not established.',snippets(result,e['status_evidence']),
                'Official source URL, opening pages, any gazette/signature/commencement information.',
                'Choose “Still unknown” if legal status cannot be established; or correct to “draft-indicated document; enactment unconfirmed” with evidence.'),
                item('evidence','Do the proposed scope passages match the PDF and support the claim?',e['description'],
                'At least one machine quotation failed exact matching. Do not approve it merely because the wording sounds plausible.',snippets(result,e['evidence']+e['applicability_evidence']),
                'Application regulation 3 and International UAS operations regulation 32. Compare the actual wording, including numbering.',
                'Choose “Correct” only after copying the actual passage and citing its PDF page. Otherwise ask the agent for a corrected evidence passage.'),
                item('scope','Should this UAS/drone proposal be included in our study?',e['topic'],
                'A rule about international drone operations may differ from the scheduled air connectivity intended by the research dataset.', '',
                'Regulation 32 and the agreed research scope. No full date of effect is established.',
                'If the study is limited to scheduled passenger/cargo airline services, propose excluding or separately categorizing UAS; explain your scope decision.')]
        status=('PDF already downloaded and read (96 pages).'
                if ident.startswith('brave') else
                'Repository download timed out. The agent found, downloaded and read an official KCAA alternative PDF. Matching title/topic does not prove an identical repository edition.')
        cards.append({'id':ident,'title':title,'route':route,'source_url':e['source_url'],
            'source_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'pdf_path':str(pdf.resolve()),
            'machine_result':str(result_path),'document_status':status,
            'repository_url': (json.loads(Path('runs/aviation-demo-20261109-schema-fix/serpapi/result.json').read_text())['documents'][int(ident.split('-')[1])-1]['source_url'] if ident.startswith('serpapi') else None),
            'reading_help':'Start with the pages named below and surrounding text. You do not need to read every page unless ambiguity or omitted evidence requires it. Request more evidence instead of guessing.',
            'items':items})
    (output/'review-pack.json').write_text(json.dumps({'cards':cards,'task':task},indent=2)+'\n')
    print(output/'review-pack.json')


if __name__=='__main__':build()
