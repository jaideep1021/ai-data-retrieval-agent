"""Apply the shadow policy to saved extraction results with zero API calls."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
from aviation_verification import RegulatoryEvent, assess
from aviation_triage import route_event, route_empty, VERSION


def execute(source, task_file, task_id, output):
    """Preserve original runs; write routing decisions and a blank human-label CSV.

    Review labels must be supplied by the researcher, not fabricated by this tool.
    All six conditions can be inspected, but only the sections condition represents
    the current selection policy. Condition pairs are not independent observations.
    """
    tasks=json.loads(task_file.read_text())
    task=next(t for t in tasks if t['task_id']==task_id)
    if not output.resolve().is_relative_to(Path('runs').resolve()):
        raise ValueError('Output must be under ignored runs/')
    files=sorted(source.glob('*-prefix.json'))+sorted(source.glob('*-sections.json'))
    if not files:
        raise ValueError('No saved replay files found')
    output.mkdir(parents=True,exist_ok=False)
    rows=[]
    for file in files:
        data=json.loads(file.read_text())
        if not data['events']:
            rows.append({'candidate_id':file.stem+'-empty','source_file':str(file),
                         'triage':route_empty()})
        for number,value in enumerate(data['events'],1):
            event=RegulatoryEvent.model_validate({k:value[k] for k in RegulatoryEvent.model_fields})
            audit=assess(event,data['selection'],task,value['source_url'])
            rows.append({'candidate_id':f'{file.stem}-{number}','source_file':str(file),
                'source_url':value['source_url'],'description':event.description,
                'audit':audit,'triage':route_event(event,audit,data['selection'],task)})
    summary={'policy_version':VERSION,'mode':'SHADOW','api_calls':0,'verified_events':0,
             'task':task,'source_hashes':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},
             'implementation_hashes':{name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in
                ['aviation_triage.py','aviation_verification.py','triage_aviation.py']},
             'all_conditions_counts':dict(Counter(r['triage']['decision'] for r in rows)),
             'current_sections_counts':dict(Counter(r['triage']['decision'] for r in rows if '-sections-' in r['candidate_id'])),
             'results':rows}
    (output/'decisions.json').write_text(json.dumps(summary,indent=2)+'\n')
    lines=['# Shadow policy review queue','',
           'No decision below is verified. Review the proposed routing as well as the event.',
           'The sections rows are the current approach; prefix rows are comparison cases.','']
    for row in rows:
        lines.extend(['## '+row['candidate_id'],'',row.get('description','No candidate'),'',
            'Decision: **'+row['triage']['decision']+'**','',
            'Reasons: '+', '.join(row['triage']['reasons']),''])
        for question in row['triage']['review_questions']:
            lines.append('- '+question)
        lines.extend(['', 'Original result: '+row['source_file'],'',
                     'Source: '+row.get('source_url','None'),''])
    (output/'review-queue.md').write_text('\n'.join(lines)+'\n')
    with (output/'human-labels.csv').open('w',newline='') as handle:
        writer=csv.writer(handle)
        writer.writerow(['candidate_id','proposed_route','human_route','event_correct_as_written',
                         'date_fields_correct','correction','evidence_reference','reviewer','reviewed_at'])
        for row in rows:
            writer.writerow([row['candidate_id'],row['triage']['decision'],'','','','','','',''])
    print(json.dumps({'all_conditions':summary['all_conditions_counts'],
                      'current_sections':summary['current_sections_counts'],'api_calls':0}))


def main():
    """Require explicit saved inputs so shadow replay cannot start live retrieval."""
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--tasks',type=Path,default=Path('examples/aviation-regulations/pilot-tasks.json'))
    parser.add_argument('--task-id',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    execute(args.source,args.tasks,args.task_id,args.output)


if __name__=='__main__':
    main()
