"""Reproducible paired development benchmark; answers never enter autonomous calls."""
import argparse
import contextlib
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import random
import statistics
import sys
import time
from types import SimpleNamespace

from dotenv import load_dotenv
from google import genai
from playwright.sync_api import sync_playwright
import requests
import serpapi

import agent
from autonomous import Retriever, StructuredModel, normalized
import multisource
from search_providers import SearchProvider

class RateLimitStop(Exception):
    """Stop evaluation instead of repeatedly consuming quota-limited calls."""


CONFIGS = ('baseline', 'autonomous_serpapi', 'autonomous_brave')


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temporary.replace(path)


def score(config, result, expected):
    """First grounded candidate is fixed policy; never choose using the answer key."""
    if config == 'baseline':
        value = result.get('retrieved_value') or None
        grounded = bool(value and result.get('evidence_valid'))
        retrieved = bool(result.get('evidence_file'))
        accepted = result.get('decision') in ('ACCEPT', 'NO_CHANGE')
        sources = int(retrieved)
    else:
        rows = result.get('sources', [])
        claims = [s for s in rows if s.get('status') == 'GROUNDED']
        value = claims[0]['claim']['value'] if claims else None
        grounded = bool(claims)
        sources = sum(bool(s.get('evidence_file')) for s in rows)
        retrieved = sources > 0
        accepted = result.get('decision') == 'AGREEMENT_OBSERVED'
    correct = bool(value and normalized(value) == normalized(expected))
    return {'candidate': value, 'correct': correct, 'grounded': grounded,
            'retrieved': retrieved, 'retrieved_pages': sources, 'accepted': accepted,
            'accepted_correct': bool(accepted and correct), 'decision': result.get('decision', 'ERROR')}


class MeteredModels:
    """Forward unchanged SDK arguments; capture usage even for the frozen baseline."""
    def __init__(self, models, pacing=None):
        self.models, self.calls = models, []
        self.pacing = pacing

    def generate_content(self, **kwargs):
        if self.pacing is not None:
            if self.pacing['rate_limited']:
                raise RateLimitStop()
            delay = self.pacing['interval'] - (time.perf_counter() - self.pacing['last'])
            if delay > 0:
                time.sleep(delay)
            self.pacing['last'] = time.perf_counter()
        record = {'model': kwargs['model']}
        self.calls.append(record)
        start = time.perf_counter()
        try:
            response = self.models.generate_content(**kwargs)
            usage = getattr(response, 'usage_metadata', None)
            record.update(status='ok', usage=usage.model_dump(mode='json') if usage else None)
            return response
        except Exception as exc:
            record.update(status='error', error_type=type(exc).__name__)
            if isinstance(getattr(exc, 'code', None), int):
                record['http_status'] = exc.code
            if getattr(exc, 'code', None) == 429 and self.pacing is not None:
                self.pacing['rate_limited'] = True
            raise
        finally:
            record['seconds'] = round(time.perf_counter() - start, 3)


class MeteredSearch:
    def __init__(self, client):
        self.client, self.calls = client, []

    def search(self, **kwargs):
        record = {'query': kwargs.get('q')}
        self.calls.append(record)
        try:
            result = self.client.search(**kwargs)
            record['status'] = 'error' if result.get('error') else 'ok'
            return result
        except Exception as exc:
            record.update(status='error', error_type=type(exc).__name__)
            raise


def usage_cost(calls, searches, provider, model):
    usages = [c['usage'] for c in calls if c.get('usage')]
    inp = sum(u.get('prompt_token_count') or 0 for u in usages)
    cached = sum(u.get('cached_content_token_count') or 0 for u in usages)
    out = sum((u.get('candidates_token_count') or 0) + (u.get('thoughts_token_count') or 0) for u in usages)
    # Standard paid-tier scenario, not an invoice; sources and assumptions in docs.
    gemini = ((inp-cached)*.30 + cached*.03 + out*2.50)/1_000_000 if model == 'gemini-3.5-flash-lite' else None
    search = searches * (.025 if provider == 'serpapi' else .005)
    return {'model_calls': len(calls), 'usage_records': len(usages), 'input_tokens': inp,
            'cached_tokens': cached, 'output_including_thinking_tokens': out,
            'search_attempts': searches, 'gemini_estimated_usd': gemini,
            'search_scenario_usd': search,
            'total_scenario_usd': search + gemini if gemini is not None else None,
            'billing_verified': False, 'usage_complete': len(usages) == len(calls)}


def summarize(rows):
    summary = {}
    for config in CONFIGS:
        items = [r for r in rows if r['config'] == config]
        if not items:
            continue
        n = len(items)
        accepted = sum(r['accepted'] for r in items)
        summary[config] = {
            'n': n, 'correct': sum(r['correct'] for r in items),
            'accuracy': sum(r['correct'] for r in items)/n,
            'retrieval_success_rate': sum(r['retrieved'] for r in items)/n,
            'grounded_coverage': sum(r['grounded'] for r in items)/n,
            'accepted': accepted, 'accepted_correct': sum(r['accepted_correct'] for r in items),
            'accepted_precision': sum(r['accepted_correct'] for r in items)/accepted if accepted else None,
            'accepted_correct_rate': sum(r['accepted_correct'] for r in items)/n,
            'mean_seconds': statistics.mean(r['seconds'] for r in items),
            'median_seconds': statistics.median(r['seconds'] for r in items),
            'total_seconds': sum(r['seconds'] for r in items),
            'decisions': {d:sum(r['decision']==d for r in items) for d in sorted({r['decision'] for r in items})},
            'search_attempts': sum(r['cost']['search_attempts'] for r in items),
            'model_calls': sum(r['cost']['model_calls'] for r in items),
            'input_tokens': sum(r['cost']['input_tokens'] for r in items),
            'output_tokens': sum(r['cost']['output_including_thinking_tokens'] for r in items),
            'usage_complete': all(r['cost']['usage_complete'] for r in items),
            'scenario_usd': sum(r['cost']['total_scenario_usd'] for r in items)
                if all(r['cost']['total_scenario_usd'] is not None for r in items) else None,
        }
    return summary


def prepare(output):
    if output.exists():
        raise ValueError('Benchmark already exists')
    response = requests.get(agent.REFERENCE_URL, timeout=25)
    response.raise_for_status()
    reference = response.json()
    excluded = {8,20,257,484,572,617,695,703}
    eligible = sorted(int(k) for k,v in reference.items() if k.isdigit() and int(k)>=100
                      and int(k) not in excluded and all(isinstance(v.get(f),str) and v[f].strip()
                          for f in ('title','status','type','created')))
    selected = random.Random(20261028).sample(eligible,20)
    observations = [{'id':f'obs-{i+1:02d}', 'pep_number':number,
                     'attribute':('title','status','type','created')[i%4],
                     'expected':reference[str(number)][('title','status','type','created')[i%4]]}
                    for i,number in enumerate(selected)]
    save(output, {'created_at':datetime.now(timezone.utc).isoformat(), 'seed':20261028,
                  'reference_url':agent.REFERENCE_URL,
                  'reference_response_sha256':hashlib.sha256(response.content).hexdigest(),
                  'eligible_count':len(eligible),'excluded_development_peps':sorted(excluded),
                  'observations':observations})


def execute(benchmark_path, output, interval=7):
    benchmark = json.loads(benchmark_path.read_text())
    output.mkdir(parents=True,exist_ok=False)
    save(output/'benchmark.json',benchmark)
    load_dotenv('.env',override=False)
    for key in ('GEMINI_API_KEY','SERPAPI_KEY','BRAVE_SEARCH_API_KEY'):
        if not os.getenv(key):
            raise ValueError('Required key missing: '+key)
    model = os.getenv('GEMINI_MODEL','gemini-3.5-flash-lite')
    agent.MODEL = model
    manifest = {'started_at':datetime.now(timezone.utc).isoformat(), 'model':model,
                'python':platform.python_version(), 'platform':platform.platform(),
                'benchmark_sha256':hashlib.sha256(benchmark_path.read_bytes()).hexdigest(),
                'source_hashes':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
                    for p in ['agent.py','autonomous.py','multisource.py','search_providers.py','evaluate.py','requirements.txt']},
                'max_sources':3, 'retry_failed_observations':False, 'minimum_model_call_interval_seconds':interval}
    save(output/'manifest.json',manifest)
    client = genai.Client(api_key=os.environ['GEMINI_API_KEY'],http_options={'timeout':60000})
    search_client = serpapi.Client(api_key=os.environ['SERPAPI_KEY'],timeout=20)
    rows=[]
    pacing={'interval':interval, 'last':0, 'rate_limited':False}
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                for i, observation in enumerate(benchmark['observations']):
                    # Rotate order to reduce simple first/last configuration bias.
                    order = CONFIGS[i%3:] + CONFIGS[:i%3]
                    for config in order:
                        run_dir = output / (observation['id']+'-'+config)
                        metered = MeteredModels(client.models,pacing)
                        proxy = SimpleNamespace(models=metered)
                        provider = 'brave' if config.endswith('brave') else 'serpapi'
                        fetcher = Retriever()
                        start=time.perf_counter()
                        if config == 'baseline':
                            run_dir.mkdir()
                            agent.EVIDENCE_DIR=run_dir/'evidence'
                            search=MeteredSearch(search_client)
                            reference={str(observation['pep_number']):{observation['attribute']:observation['expected']}}
                            with contextlib.redirect_stdout(io.StringIO()):
                                result=agent.process_record({'pep_number':observation['pep_number'],
                                    'attribute':observation['attribute'],'current_value':''},browser,reference,search,proxy)
                            calls=len(search.calls)
                            save(run_dir/'result.json',result)
                            save(run_dir/'search_usage.json',search.calls)
                        else:
                            search=SearchProvider(provider,client=search_client if provider=='serpapi' else None,
                                                  key=os.getenv('BRAVE_SEARCH_API_KEY') if provider=='brave' else None)
                            try:
                                result=multisource.run(f"PEP {observation['pep_number']}",observation['attribute'],
                                    StructuredModel(proxy,model),[search],fetcher,run_dir,max_sources=3)
                            finally:
                                fetcher.session.close()
                            calls=len(result['search_attempts'])
                        elapsed=round(time.perf_counter()-start,3)
                        save(run_dir/'model_usage.json',metered.calls)
                        row={**observation,'config':config,**score(config,result,observation['expected']),
                             'seconds':elapsed,'cost':usage_cost(metered.calls,calls,provider,model),
                             'artifact':str(run_dir.relative_to(output))}
                        rows.append(row)
                        save(output/'observations.json',rows)
                        save(output/'summary.json',summarize(rows))
                        if pacing['rate_limited']:
                            manifest.update(stopped_reason='Gemini HTTP 429', completed_trials=len(rows))
                            save(output/'manifest.json',manifest)
                            raise RateLimitStop()
                        print(f"{len(rows)}/60 {observation['id']} {config}: {row['decision']}, correct={row['correct']}, {elapsed}s",flush=True)
                manifest['completed_at']=datetime.now(timezone.utc).isoformat()
                save(output/'manifest.json',manifest)
            finally:
                browser.close()
    finally:
        client.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','run','summarize'])
    parser.add_argument('--benchmark',type=Path,default=Path('examples/evaluation-20.json'))
    parser.add_argument('--output-dir',type=Path)
    parser.add_argument('--model-interval',type=float,default=7,help='Minimum seconds between model calls')
    args=parser.parse_args()
    if args.action=='prepare':
        prepare(args.benchmark)
    elif args.action=='summarize':
        if not args.output_dir: parser.error('--output-dir required')
        save(args.output_dir/'summary.json',summarize(json.loads((args.output_dir/'observations.json').read_text())))
    else:
        if args.model_interval < 0: parser.error('Model interval cannot be negative')
        execute(args.benchmark,args.output_dir or Path('runs')/('evaluation-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')),args.model_interval)


if __name__=='__main__':
    try:
        main()
    except Exception as exc:
        print(f'Evaluation stopped ({type(exc).__name__}); private exception text omitted.',file=sys.stderr)
        raise SystemExit(1)
