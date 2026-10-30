"""Build a sanitized Markdown report from a saved evaluation, with no API calls."""
import argparse
from collections import Counter
import json
from pathlib import Path

from evaluate import summarize


def failure_labels(row, detail):
    labels=[]
    if row['decision']=='ERROR':
        labels.append('run error: '+str(detail.get('error_stage') or detail.get('stage') or 'unknown'))
    if not row['retrieved']:
        labels.append('no captured page')
    elif not row['grounded']:
        labels.append('no grounded candidate')
    elif not row['correct']:
        labels.append('candidate differs from reference')
    if row['correct'] and not row['accepted']:
        labels.append('correct candidate, not accepted')
    if row['decision']=='CONFLICT':
        labels.append('grounded strings differ; semantic review required')
    for source in detail.get('sources',[]):
        if source.get('error_type'):
            labels.append('source '+source.get('stage','unknown')+': '+source['error_type'])
    for attempt in detail.get('search_attempts',[]):
        if attempt.get('status')=='error':
            labels.append('search provider error')
    return sorted(set(labels))


def build(run_dir, output):
    rows=json.loads((run_dir/'observations.json').read_text())
    manifest=json.loads((run_dir/'manifest.json').read_text())
    summary=summarize(rows)
    sanitized=[]
    for row in rows:
        detail=json.loads((run_dir/row['artifact']/'result.json').read_text())
        sanitized.append({**row,'failure_labels':failure_labels(row,detail)})
    report={'run':run_dir.name,'manifest':manifest,'summary':summary,'observations':sanitized}
    output.mkdir(parents=True,exist_ok=True)
    (output/'evaluation-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    pct=lambda x:'undefined' if x is None else f'{100*x:.1f}%'
    lines=['# Deliverable 3 — measured findings','',
        f"Run: `{run_dir.name}`. Completed trials: **{len(rows)}/60**.",
        f"Completion recorded: **{'yes' if manifest.get('completed_at') else 'no'}**.",'',
        '## Results','',
        '| Configuration | Correct / N | Candidate accuracy | Retrieval | Accepted correct / N | Accepted precision | Mean seconds | Median seconds | Cost scenario USD |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for config,s in summary.items():
        cost='unknown' if s['scenario_usd'] is None else f"${s['scenario_usd']:.4f}"
        lines.append(f"| {config} | {s['correct']}/{s['n']} | {pct(s['accuracy'])} | {pct(s['retrieval_success_rate'])} | {s['accepted_correct']}/{s['n']} | {pct(s['accepted_precision'])} | {s['mean_seconds']:.2f} | {s['median_seconds']:.2f} | {cost} |")
    lines += ['', 'Candidate accuracy uses the first grounded autonomous claim, even if the system',
        'abstained or found a conflict. Accepted-correct rate measures the more restrictive',
        'output decision. Neither measure proves publisher independence. Times include',
        'configured model-call pacing. Cost scenarios are not verified bills; see protocol.',
        '', '## Decisions and usage','',
        '| Configuration | Decisions | Search attempts | Model calls | Input tokens | Output + thinking tokens | Usage complete |',
        '|---|---|---:|---:|---:|---:|---|']
    for config,s in summary.items():
        decisions=', '.join(f'{k}: {v}' for k,v in s['decisions'].items())
        lines.append(f"| {config} | {decisions} | {s['search_attempts']} | {s['model_calls']} | {s['input_tokens']} | {s['output_tokens']} | {s['usage_complete']} |")
    lines += ['', '## Attribute breakdown','',
        '| Configuration | Attribute | Correct / N |','|---|---|---:|']
    for config in summary:
        for attr in ('title','status','type','created'):
            selected=[r for r in rows if r['config']==config and r['attribute']==attr]
            lines.append(f"| {config} | {attr} | {sum(r['correct'] for r in selected)}/{len(selected)} |")
    lines += ['', '## Failure and abstention inventory','',
        'Labels may overlap within one trial. They describe observed symptoms, not an',
        'automated determination that the source or model is factually wrong.','',
        '| Observation | PEP / field | Configuration | Decision | Diagnostic |',
        '|---|---|---|---|---|']
    for row in sanitized:
        if row['failure_labels']:
            lines.append(f"| {row['id']} | {row['pep_number']} / {row['attribute']} | {row['config']} | {row['decision']} | {'; '.join(row['failure_labels'])} |")
    lines += ['', '## Boundaries','',
        '- One frozen development sample of 20 PEPs, five records per field; no business-domain claim.',
        '- Prior demonstration PEPs excluded; model pretraining contamination remains possible.',
        '- Baseline uses a reference oracle for acceptance and known-domain fallback. Autonomous modes do not.',
        '- Rotated order does not eliminate changing web results, service caches, or stochastic model behavior.',
        '- Raw page evidence, provider results, and keys remain local and excluded from this report.',
        '- Separate initial quota-limited run is preserved and must not be pooled with this run.',
        '- See evaluation-step3.md for exact scoring, sampling, reproduction, and pricing assumptions.','']
    (output/'evaluation-step3-findings.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_dir',type=Path)
    parser.add_argument('--output-dir',type=Path,default=Path('docs'))
    args=parser.parse_args()
    build(args.run_dir,args.output_dir)
