"""Build a portable, private HTML review workspace from saved candidate evidence.

No server, model calls or credentials. The generated workspace belongs under runs/;
only this builder and its template are suitable for repository publication.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil


def build(source, output):
    """Package current section candidates, evidence, documents and prior AI notes.

    Preserve original machine output and human-label CSV. Edits in the interface
    export to a separate JSON review record, never silently overwrite research data.
    """
    if not output.resolve().is_relative_to(Path('runs').resolve()):
        raise ValueError('Private review output must be under runs/')
    decisions=json.loads((source/'decisions.json').read_text())
    labels_path=source/'human-labels.csv'
    labels={r['candidate_id']:r for r in csv.DictReader(labels_path.open())} if labels_path.exists() else {}
    output.mkdir(parents=True,exist_ok=False)
    cards=[]
    for row in decisions['results']:
        if '-sections-' not in row['candidate_id']:
            continue
        saved=Path(row['source_file'])
        result=json.loads(saved.read_text())
        index=int(row['candidate_id'].rsplit('-',1)[1])-1
        event=result['events'][index]
        replay=json.loads((saved.parent/'manifest.json').read_text())
        provider,number,_=saved.stem.split('-')
        original=Path(replay['source_run'])/provider
        text=(original/f'document-{number}.txt').read_text()
        raw=original/f'document-{number}.bin'
        document=json.loads((original/'result.json').read_text())['documents'][int(number)-1]
        if hashlib.sha256(raw.read_bytes()).hexdigest()!=document['raw_sha256']:
            raise ValueError('Source document hash mismatch')
        filename=f'{provider}-{number}.pdf' if raw.read_bytes().startswith(b'%PDF-') else None
        if filename:
            shutil.copyfile(raw,output/filename)
        cards.append({**row,'event':event,'sections':result['selection']['sections'],
            'coverage':{k:v for k,v in result['selection'].items() if k!='sections'},
            'full_text':text,'local_pdf':filename,'source_sha256':document['raw_sha256'],
            'prior_review':labels.get(row['candidate_id'])})
    payload={'task':decisions['task'],'cards':cards,'policy_version':decisions['policy_version']}
    # Escape markup delimiters to prevent retrieved text terminating the data block.
    encoded=json.dumps(payload).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    template=Path('review_ui/aviation.html').read_text()
    (output/'index.html').write_text(template.replace('__REVIEW_DATA__',encoded))
    print(f'Created {output}/index.html with {len(cards)} current candidates; original records unchanged.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    build(args.source,args.output)
