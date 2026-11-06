"""Recheck saved claims without new searches, model calls, or reference access.

This is an offline validator replay, not another independent experiment. Source
acquisition time and usage are inherited and must not be charged or counted twice.
Run evaluate_business.py score separately, after the replay is persisted.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

from business_agent import BusinessClaim, VERSION, assess_claim, compare_sources, save_json


def replay(source, output):
    manifest = json.loads((source / 'manifest.json').read_text())
    if manifest['status'] != 'COMPLETE':
        raise ValueError('Replay only a complete paired run')
    output.mkdir(parents=True, exist_ok=False)
    for name in manifest['artifacts']:
        shutil.copytree(source/name, output/name)
        path = output/name/'result.json'
        result = json.loads(path.read_text())
        result['original_decision'] = result['decision']
        result['acquisition_version'] = result['version']
        result['version'] = VERSION
        result['validation_mode'] = 'OFFLINE_REPLAY_NO_NEW_API_CALLS'
        for row in result['sources']:
            if 'claim' not in row or not row.get('evidence_file'):
                continue
            text = (output/name/row['evidence_file']).read_text()
            context = '\n[EXCERPT BREAK]\n'.join(text[a:b] for a,b in row['context_offsets'])
            row.update(assess_claim(BusinessClaim(**row['claim']), context, result['input']))
            row['status'] = 'GROUNDED' if row['numeric_grounded'] else 'UNSUPPORTED'
        candidates = [r for r in result['sources'] if r.get('numeric_grounded')]
        result['candidate_source_id'] = candidates[0]['id'] if candidates else None
        if result['original_decision'] != 'ERROR':
            result.update(compare_sources(result['sources']))
        result['replayed_at'] = datetime.now(timezone.utc).isoformat()
        save_json(path,result)
    manifest.update(acquisition_run=source.name, acquisition_version=manifest['version'],
                    version=VERSION, mode='OFFLINE_VALIDATION_REPLAY',
                    incremental_search_calls=0, incremental_model_calls=0,
                    reused_acquisition_time_and_usage=True,
                    validator_sha256=hashlib.sha256(Path('business_agent.py').read_bytes()).hexdigest())
    save_json(output/'manifest.json',manifest)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    replay(args.source,args.output_dir)
