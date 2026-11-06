"""Week 3 runner and offline scorer, deliberately separate operations.

`run` reads only question inputs and credentials. `score` reads saved results and
then references; it makes no network calls. Separate commands make answer access
reviewable and prevent accidental answer fields from entering the model prompt.
"""
import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
import time
from types import SimpleNamespace

from dotenv import load_dotenv
from google import genai
import serpapi

from autonomous import StructuredModel
from business_agent import (BatchStop, BudgetExceeded, BusinessInput, BusinessRetriever, VERSION, decimal_value,
                            run, save_json)
from search_providers import SearchProvider

# These IDs specify the development split, not reference values or source URLs.
DEVELOPMENT_IDS = tuple(f'airfare-{n:02d}' for n in range(1, 7))


class PacedModels:
    """Share pacing across trials and retain usage even if JSON parsing fails."""
    def __init__(self, models, interval=7):
        self.models, self.interval, self.last = models, interval, None
        self.calls = []
        self.trial_start = 0
        self.batch_limit = 120
        self.trial_limit = 12

    def generate_content(self, **kwargs):
        """At most one retry for 500/502/503/504; count every actual attempt.

        No retries for quota/auth errors. Shared caps include retry attempts,
        so a transient service error cannot silently multiply the batch spend.
        """
        for attempt in range(2):
            if len(self.calls) >= self.batch_limit:
                raise BatchStop('BATCH_REQUEST_LIMIT')
            if len(self.calls) - self.trial_start >= self.trial_limit:
                raise BudgetExceeded('TRIAL_REQUEST_LIMIT')
            if self.last is not None:
                time.sleep(max(0, self.interval - (time.perf_counter() - self.last)))
            self.last = time.perf_counter()
            record = {'model': kwargs['model'], 'attempt': attempt + 1,
                      'started_at': datetime.now(timezone.utc).isoformat()}
            self.calls.append(record)
            started = time.perf_counter()
            try:
                kwargs['config'] = {**kwargs['config'], 'max_output_tokens': 2048}
                response = self.models.generate_content(**kwargs)
                usage = getattr(response, 'usage_metadata', None)
                record.update(status='ok', usage=usage.model_dump(mode='json') if usage else None)
                return response
            except Exception as exc:
                code = getattr(exc, 'code', None)
                record.update(status='error', error_type=type(exc).__name__, http_status=code)
                if attempt == 0 and code in (500, 502, 503, 504):
                    record['retry_wait_seconds'] = 10
                    time.sleep(10)
                else:
                    raise
            finally:
                record['seconds'] = round(time.perf_counter() - started, 3)


def load_inputs(path):
    """Validate every row, including duplicate IDs, before any paid call."""
    rows = json.loads(Path(path).read_text())
    tasks = [BusinessInput.model_validate(row).model_dump() for row in rows]
    if len({t['record_id'] for t in tasks}) != len(tasks):
        raise ValueError('Duplicate task IDs')
    return tasks


def execute(inputs, output, providers, ids, interval=7):
    """Rotate provider order and stop on auth/quota errors; never auto-rerun."""
    tasks = load_inputs(inputs)
    selected = [t for t in tasks if t['record_id'] in ids]
    if not selected or {t['record_id'] for t in selected} != set(ids):
        raise ValueError('Requested task IDs missing')
    if len(set(providers)) != len(providers) or not set(providers) <= {'serpapi', 'brave'}:
        raise ValueError('Invalid providers')
    load_dotenv('.env', override=False)
    needed = ['GEMINI_API_KEY'] + ['SERPAPI_KEY' if p == 'serpapi' else 'BRAVE_SEARCH_API_KEY' for p in providers]
    if any(not os.getenv(name) for name in needed):
        raise ValueError('Required credential missing')
    output.mkdir(parents=True, exist_ok=False)
    model_name = os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite')
    manifest = {'version': VERSION, 'started_at': datetime.now(timezone.utc).isoformat(),
                'model': model_name, 'task_ids': ids, 'providers': providers,
                'inputs_sha256': hashlib.sha256(Path(inputs).read_bytes()).hexdigest(),
                'source_hashes': {name: hashlib.sha256(Path(name).read_bytes()).hexdigest()
                    for name in ['business_agent.py', 'evaluate_business.py', 'autonomous.py',
                                 'multisource.py', 'search_providers.py', 'requirements.txt',
                                 'business_documents.py', 'requirements-business.txt']},
                'reference_used': False, 'model_interval_seconds': interval,
                'limits_per_trial': {'searches': 2, 'sources': 3, 'logical_model_calls': 10, 'model_http_attempts': 12},
                'batch_model_http_attempt_limit': 120, 'transient_retries_per_call': 1,
                'planned_trials': len(selected) * len(providers), 'completed_trials': 0,
                'status': 'RUNNING', 'artifacts': []}
    save_json(output / 'manifest.json', manifest)
    # Disable SDK retries: each recorded call must correspond to one attempt,
    # and a quota response must reach our stop logic immediately.
    client = genai.Client(api_key=os.environ['GEMINI_API_KEY'],
                         http_options={'timeout': 60000, 'retry_options': {'attempts': 1}})
    metered = PacedModels(client.models, interval)
    try:
        for i, task in enumerate(selected):
            shift = i % len(providers)
            order = providers[shift:] + providers[:shift]
            for name in order:
                trial = output / f'{task["record_id"]}-{name}'
                provider = (SearchProvider(name, client=serpapi.Client(api_key=os.environ['SERPAPI_KEY'], timeout=20))
                            if name == 'serpapi' else SearchProvider(name, key=os.environ['BRAVE_SEARCH_API_KEY']))
                fetcher = BusinessRetriever()
                offset = len(metered.calls)
                metered.trial_start = offset
                try:
                    result = run(task, StructuredModel(SimpleNamespace(models=metered), model_name),
                                 provider, fetcher, trial)
                finally:
                    fetcher.session.close()
                    if trial.exists():
                        save_json(trial / 'model-usage.json', metered.calls[offset:])
                manifest['completed_trials'] += 1
                manifest['artifacts'].append(trial.name)
                save_json(output / 'manifest.json', manifest)
                print(f'{manifest["completed_trials"]}/{manifest["planned_trials"]} '
                      f'{task["record_id"]} {name}: {result["decision"]}', flush=True)
                if result['stop_batch']:
                    manifest.update(status='STOPPED', stop_reason='Authentication or quota/provider error')
                    return
        manifest['status'] = 'COMPLETE'
    except BaseException as exc:
        manifest.update(status='INTERRUPTED', error_type=type(exc).__name__)
        raise
    finally:
        manifest['ended_at'] = datetime.now(timezone.utc).isoformat()
        save_json(output / 'manifest.json', manifest)
        client.close()


def score_trial(result, reference):
    """Score the preselected candidate, then the actual accepted value separately."""
    source_id = result['candidate_source_id']
    source = next((s for s in result['sources'] if s['id'] == source_id), None)
    value = source['claim']['value'] if source else None
    def correct(number):
        return number is not None and abs(decimal_value(number) - Decimal(reference['expected'])) <= Decimal(reference['absolute_tolerance'])
    numeric_correct = correct(value)
    contextual = bool(numeric_correct and source and source['context_match'])
    accepted = result['decision'] == 'AGREEMENT_OBSERVED'
    accepted_correct = accepted and correct(result.get('accepted_value'))
    return {'record_id': result['input']['record_id'], 'provider': result['provider'],
            'split': reference['split'], 'condition': result['input']['condition'],
            'attribute': result['input']['attribute'], 'candidate': value,
            'numeric_correct': numeric_correct, 'context_correct': contextual,
            'retrieved': any(s.get('evidence_file') for s in result['sources']),
            'accepted': accepted, 'accepted_correct': bool(accepted_correct),
            'incorrect_accepted': bool(accepted and not accepted_correct),
            'decision': result['decision'], 'seconds': result['seconds'],
            'search_attempts': len(result['search_attempts']),
            'search_successes': sum(a['status'] == 'ok' for a in result['search_attempts']),
            'failure_labels': sorted({label for s in result['sources'] for label in s.get('failure_labels', [])}),
            'error_type': result.get('error_type')}


def usage_estimate(calls, searches, provider, rates):
    """No guessed prices: supplied rates define a scenario, not actual billing."""
    usages = [c['usage'] for c in calls if c.get('usage')]
    inputs = sum(u.get('prompt_token_count') or 0 for u in usages)
    cached = sum(u.get('cached_content_token_count') or 0 for u in usages)
    outputs = sum((u.get('candidates_token_count') or 0) + (u.get('thoughts_token_count') or 0) for u in usages)
    complete = len(usages) == len(calls)
    keys = [provider + '_per_search', 'model_input_per_million', 'model_cached_per_million', 'model_output_per_million']
    priced = all(k in rates for k in keys)
    cost = ((inputs-cached)*rates[keys[1]] + cached*rates[keys[2]] + outputs*rates[keys[3]])/1e6 + searches*rates[keys[0]] if priced else None
    return {'model_calls': len(calls), 'input_tokens': inputs, 'cached_tokens': cached,
            'output_including_thinking_tokens': outputs, 'usage_complete': complete,
            'estimated_usd': cost if complete else None, 'billing_verified': False}


def summarize(rows):
    """Denominators are attempted trials; unrun trials are reported separately."""
    groups = {}
    for dimension in ('provider', 'split', 'condition', 'attribute'):
        groups[dimension] = {}
        for value in sorted({r[dimension] for r in rows}):
            subset = [r for r in rows if r[dimension] == value]
            n = len(subset)
            counts = {key: sum(r[key] for r in subset) for key in
                      ('numeric_correct', 'context_correct', 'retrieved', 'accepted', 'accepted_correct', 'incorrect_accepted')}
            costs = [r['usage']['estimated_usd'] for r in subset]
            total = sum(costs) if all(c is not None for c in costs) else None
            groups[dimension][value] = {'n': n, **counts,
                'accuracy': counts['context_correct']/n, 'retrieval_success_rate': counts['retrieved']/n,
                'unresolved_rate': (n-counts['accepted'])/n,
                'accepted_precision': counts['accepted_correct']/counts['accepted'] if counts['accepted'] else None,
                'mean_seconds': statistics.mean(r['seconds'] for r in subset),
                'median_seconds': statistics.median(r['seconds'] for r in subset),
                'estimated_usd': total,
                'cost_per_correct_accepted': total/counts['accepted_correct'] if total is not None and counts['accepted_correct'] else None}
    return groups


def score_directory(output, references, rates):
    """Read persisted results before opening the reference manifest."""
    manifest = json.loads((output / 'manifest.json').read_text())
    saved = [(name, json.loads((output / name / 'result.json').read_text())) for name in manifest['artifacts']]
    reference_rows = json.loads(references.read_text())['cases']
    lookup = {r['record_id']: r for r in reference_rows}
    rows = []
    for name, result in saved:
        row = score_trial(result, lookup[result['input']['record_id']])
        row['usage'] = usage_estimate(json.loads((output / name / 'model-usage.json').read_text()),
                                      row['search_attempts'], row['provider'], rates)
        rows.append(row)
    report = {'run_status': manifest['status'],
              'mode': manifest.get('mode', 'LIVE_ACQUISITION'),
              'acquisition_run': manifest.get('acquisition_run', output.name),
              'reused_acquisition_time_and_usage': manifest.get('reused_acquisition_time_and_usage', False),
              'incremental_model_calls': 0 if manifest.get('mode') == 'OFFLINE_VALIDATION_REPLAY' else None,
              'planned_trials': manifest['planned_trials'],
              'attempted_trials': len(rows), 'unrun_trials': manifest['planned_trials'] - len(rows),
              'reference_sha256': hashlib.sha256(references.read_bytes()).hexdigest(),
              'rates_scenario': rates, 'billing_verified': False,
              'observations': rows, 'summary': summarize(rows)}
    save_json(output / 'scored-results.json', report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check', 'run', 'score'])
    parser.add_argument('--inputs', type=Path, default=Path('examples/week3/agent-inputs.json'))
    parser.add_argument('--references', type=Path, default=Path('examples/week3/evaluator-manifest.json'))
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--providers', nargs='+', choices=['serpapi', 'brave'], default=['serpapi', 'brave'])
    parser.add_argument('--ids', nargs='+', default=list(DEVELOPMENT_IDS))
    parser.add_argument('--model-interval', type=float, default=7)
    parser.add_argument('--rates', type=Path, help='Optional JSON of explicit USD rate assumptions')
    args = parser.parse_args(argv)
    if args.model_interval < 7:
        parser.error('Keep at least seven seconds between model calls')
    if args.action == 'check':
        tasks = load_inputs(args.inputs)
        print(json.dumps({'valid_inputs': len(tasks), 'selected_ids': args.ids, 'live_calls': 0}))
    elif args.action == 'run':
        if not args.output_dir:
            parser.error('--output-dir required; use a new runs/ folder')
        execute(args.inputs, args.output_dir, args.providers, args.ids, args.model_interval)
    else:
        if not args.output_dir:
            parser.error('--output-dir required')
        rates = json.loads(args.rates.read_text()) if args.rates else {}
        if any(not isinstance(v, (int, float)) or v < 0 for v in rates.values()):
            parser.error('Rates must be nonnegative numbers')
        report = score_directory(args.output_dir, args.references, rates)
        print(json.dumps({'attempted': report['attempted_trials'], 'unrun': report['unrun_trials']}))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'Business evaluation stopped ({type(exc).__name__}); private error text omitted.', file=sys.stderr)
        raise SystemExit(1)
