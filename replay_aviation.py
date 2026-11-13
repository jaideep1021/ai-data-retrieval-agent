"""Diagnostic replay of already-discovered documents; never autonomous search.

Compare prefix versus whole-document section selection with the same new schema.
Original machine outputs are retained separately for a descriptive comparison.
No source URLs, regulatory dates or answers are supplied from researcher findings.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

from dotenv import load_dotenv
from google import genai
from autonomous import StructuredModel
from evaluate_business import PacedModels
from business_agent import save_json
from aviation_verification import extract_review, VERSION


def execute(source, output):
    """Replay all readable saved documents, bounding attempts and saving each result.

    Source-byte hashes are checked before calls. Text hashes record exactly which
    saved extraction was used, but do not prove the parser captured all PDF content.
    Outputs must be local runs/ paths and never overwrite a prior experiment.
    """
    if not output.resolve().is_relative_to(Path('runs').resolve()):
        raise ValueError('Output must be under runs/')
    inputs=[]
    for provider in ['serpapi','brave']:
        original=json.loads((source/provider/'result.json').read_text())
        for number,doc in enumerate(original['documents'],1):
            if doc['status']!='READ':
                continue
            raw=(source/provider/f'document-{number}.bin').read_bytes()
            if hashlib.sha256(raw).hexdigest()!=doc['raw_sha256']:
                raise ValueError('Original document hash mismatch')
            text_path=source/provider/f'document-{number}.txt'
            inputs.append((provider,number,original['task'],doc,text_path.read_text()))
    if not inputs or len(inputs)>3:
        raise ValueError('This development replay permits one to three saved documents')
    load_dotenv('.env',override=True)
    if not os.getenv('GEMINI_API_KEY'):
        raise ValueError('Gemini key missing')
    output.mkdir(parents=True,exist_ok=False)
    client=genai.Client(api_key=os.environ['GEMINI_API_KEY'],
        http_options={'timeout':60000,'retry_options':{'attempts':1}})
    paced=PacedModels(client.models,interval=7)
    paced.batch_limit=12
    paced.trial_limit=2
    model=StructuredModel(SimpleNamespace(models=paced),os.getenv('GEMINI_MODEL','gemini-3.5-flash-lite'))
    manifest={'version':VERSION,'experiment':'SAVED_DOCUMENT_EXTRACTION_REPLAY',
        'autonomous_search':False,'search_calls':0,'model':model.model,
        'started_at':datetime.now(timezone.utc).isoformat(),'status':'RUNNING',
        'attempt_cap':12,'interval_seconds':7,'source_run':str(source),'results':[],
        'source_hashes':{name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in
            ['aviation_verification.py','aviation_triage.py','replay_aviation.py','autonomous.py','evaluate_business.py']}}
    try:
        for i,(provider,number,task,doc,text) in enumerate(inputs):
            # Alternate order to reduce a consistent prefix-first timing advantage.
            modes=['prefix','sections'] if i%2==0 else ['sections','prefix']
            for mode in modes:
                paced.trial_start=len(paced.calls)
                name=f'{provider}-{number}-{mode}'
                record={'id':name,'raw_sha256':doc['raw_sha256'],
                        'text_sha256':hashlib.sha256(text.encode()).hexdigest()}
                try:
                    result=extract_review(task,text,doc['source_url'],model,mode)
                    save_json(output/f'{name}.json',result)
                    record.update(status='OK',events=len(result['events']))
                except Exception as exc:
                    record.update(status='ERROR',error_type=type(exc).__name__,http_status=getattr(exc,'code',None))
                    if record['http_status'] in (400,401,403,429) or type(exc).__name__=='BatchStop':
                        manifest['results'].append(record)
                        manifest['status']='STOPPED'
                        return
                manifest['results'].append(record)
                save_json(output/'manifest.json',manifest)
                print(f'{name}: {record["status"]}',flush=True)
        manifest['status']='FINISHED'
    finally:
        manifest['ended_at']=datetime.now(timezone.utc).isoformat()
        save_json(output/'manifest.json',manifest)
        save_json(output/'model-usage.json',paced.calls)
        client.close()


def main():
    """Select saved inputs explicitly, without accepting arbitrary answer fields."""
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    execute(args.source,args.output)


if __name__=='__main__':
    main()
