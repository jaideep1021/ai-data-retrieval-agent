"""Offline audit of saved Week 2 decisions; never reruns models or changes scores.

Run from the repository root. Raw run folders must be present locally.
Only selected public benchmark fields and source statuses enter the output.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path


def main():
    report_path = Path('docs/evaluation-results.json')
    report = json.loads(report_path.read_text())
    run = Path('runs') / report['run']
    cases = []
    verified = 0
    for observation in report['observations']:
        if observation['config'] == 'baseline':
            continue
        path = run / observation['artifact'] / 'result.json'
        result = json.loads(path.read_text())
        assert result['decision'] == observation['decision']
        sources = result.get('sources', [])
        grounded = [s for s in sources if s['status'] == 'GROUNDED']
        # Verify original saved evidence without publishing its contents.
        for source in sources:
            if source.get('evidence_file'):
                raw = (path.parent / source['evidence_file']).read_bytes()
                assert hashlib.sha256(raw).hexdigest() == source['sha256']
                verified += 1
        correct_rejected = observation['correct'] and not observation['accepted']
        if correct_rejected:
            if result['decision'] == 'INSUFFICIENT_EVIDENCE':
                assert len(grounded) == 1
                reason = 'ONE_USABLE_GROUNDED_SOURCE'
            elif result['decision'] == 'CONFLICT':
                assert observation['pep_number'] == 467
                reason = 'TITLE_PREFIX_CONFLICT_MANUALLY_REVIEWED'
            else:
                raise AssertionError('Unreviewed rejection category')
        elif observation['accepted']:
            reason = 'ACCEPTED'
        elif observation['candidate'] is not None:
            reason = 'CANDIDATE_DIFFERS_UNDER_ORIGINAL_SCORING'
        else:
            reason = 'NO_GROUNDED_CANDIDATE'
        cases.append({
            'id': observation['id'], 'pep_number': observation['pep_number'],
            'attribute': observation['attribute'], 'provider': observation['config'],
            'candidate_correct': observation['correct'], 'accepted': observation['accepted'],
            'decision': result['decision'], 'reason': reason,
            'grounded_sources': len(grounded),
            'source_statuses': dict(Counter(s['status'] for s in sources)),
            'grounded_source_urls': [s['final_url'] for s in grounded],
            'artifact': observation['artifact'],
            'result_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    rejected = [c for c in cases if c['candidate_correct'] and not c['accepted']]
    assert len(cases) == 40 and len(rejected) == 13
    output = {
        'method': 'Offline audit; original candidate scores and decisions unchanged',
        'source_run': report['run'],
        'original_report_sha256': hashlib.sha256(report_path.read_bytes()).hexdigest(),
        'autonomous_trials': len(cases), 'correct_not_accepted': len(rejected),
        'rejection_reasons': dict(Counter(c['reason'] for c in rejected)),
        'verified_evidence_files': verified, 'cases': cases,
    }
    Path('docs/week3-rejection-audit.json').write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps({k: v for k, v in output.items() if k != 'cases'}, indent=2))


if __name__ == '__main__':
    main()
