"""Run one record through the Week 3 structured adapter without reference access."""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path

from dotenv import load_dotenv
import serpapi

from evaluate_business import load_inputs
from search_providers import SearchProvider
from structured_retrieval import run


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record-id',required=True)
    parser.add_argument('--inputs',type=Path,default=Path('examples/week3/agent-inputs.json'))
    parser.add_argument('--provider',choices=['serpapi','brave','socrata'],default='socrata')
    parser.add_argument('--output-dir',type=Path)
    args=parser.parse_args()
    tasks=[r for r in load_inputs(args.inputs) if r['record_id']==args.record_id]
    if len(tasks)!=1:parser.error('Record ID must select exactly one input')
    provider=args.provider
    if provider!='socrata':
        load_dotenv('.env',override=False)
        key='SERPAPI_KEY' if provider=='serpapi' else 'BRAVE_SEARCH_API_KEY'
        if not os.getenv(key):parser.error('Required environment variable missing: '+key)
        provider=(SearchProvider('serpapi',client=serpapi.Client(api_key=os.environ[key],timeout=20))
                  if provider=='serpapi' else SearchProvider('brave',key=os.environ[key]))
    output=args.output_dir or Path('runs')/('structured-record-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    result=run(tasks[0],provider,output)
    print(json.dumps({'record_id':args.record_id,'decision':result['decision'],
                      'value':result.get('accepted_value'),'seconds':result['seconds'],
                      'evidence':str(output/'result.json')},indent=2))


if __name__=='__main__':main()
