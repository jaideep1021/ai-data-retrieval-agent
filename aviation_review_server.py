"""Local-only review form that submits field decisions to the real labels CSV.

Bind exclusively to loopback. Origin/Host checks plus a per-process token prevent
cross-site writes. Only explicitly packaged documents can be served. No model/API
calls are made. CSV writes are atomic, with backups and a separate submission log.
"""
import argparse
import csv
from datetime import datetime
import io
import json
import os
from pathlib import Path
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit, parse_qs
from zoneinfo import ZoneInfo


BASE_FIELDS=['candidate_id','proposed_route','human_route','event_correct_as_written',
 'date_fields_correct','correction','evidence_reference','reviewer','reviewed_at']
EXTRA_FIELDS=['review_decision','reviewed_source_sha256','field_reviews_json','review_coverage','overall_note']


def validate_submission(payload, cards):
    """Require explicit decisions and evidence for corrections; do not infer approval."""
    if not isinstance(payload,dict):raise ValueError('Invalid submission')
    card=next((c for c in cards if c['id']==payload.get('candidate_id')),None)
    if not card or payload.get('source_sha256')!=card['source_sha256']:
        raise ValueError('Document changed or candidate unknown. Reload the page.')
    for name in ['reviewer','notes','coverage','decision']:
        if not isinstance(payload.get(name),str) or len(payload[name])>5000:
            raise ValueError('Missing or invalid '+name)
    if not payload['reviewer'].strip():raise ValueError('Enter your reviewer name.')
    if payload['coverage'] not in ['passages','whole_document','additional_sources']:
        raise ValueError('Choose what you inspected.')
    if payload['decision'] not in ['supported','corrected','more_evidence','exclude']:
        raise ValueError('Choose an overall decision.')
    fields=payload.get('fields')
    if not isinstance(fields,dict) or set(fields)!={i['id'] for i in card['items']}:
        raise ValueError('Complete each displayed review item.')
    for value in fields.values():
        if not isinstance(value,dict):raise ValueError('Invalid field decision')
        if value.get('decision') not in ['keep','correct','unknown','exclude']:
            raise ValueError('Choose a decision for every review item.')
        for key in ['value','reference','quote','reason']:
            if not isinstance(value.get(key),str) or len(value[key])>10000:
                raise ValueError('Invalid review text')
        if value['decision']=='correct' and not all(value[k].strip() for k in ['value','reference','quote']):
            raise ValueError('Each correction needs a value, source/page and supporting passage.')
    if payload['decision']=='supported' and any(v['decision']!='keep' for v in fields.values()):
        raise ValueError('Supported as written requires keeping every displayed field. Otherwise select corrections or more evidence.')
    if payload['decision']=='corrected' and not any(v['decision']=='correct' for v in fields.values()):
        raise ValueError('Record at least one field correction, or choose another outcome.')
    return card


def safe_cell(value):
    """Prevent spreadsheet formula execution when user text is opened in Excel."""
    return "'"+value if value.lstrip().startswith(('=','+','-','@')) else value


def save_submission(path, card, payload):
    """Update exactly one row; preserve old columns, other rows and prior revisions."""
    now=datetime.now(ZoneInfo('America/New_York')).isoformat()
    old=path.read_bytes() if path.exists() else b''
    reader=csv.DictReader(io.StringIO(old.decode('utf-8')))
    rows=list(reader);columns=list(reader.fieldnames or BASE_FIELDS)
    for field in BASE_FIELDS+EXTRA_FIELDS:
        if field not in columns:columns.append(field)
    row=next((r for r in rows if r['candidate_id']==card['id']),None)
    if row is None:
        row={k:'' for k in columns};row['candidate_id']=card['id'];rows.append(row)
    route={'supported':'WOULD_ACCEPT','corrected':'NEEDS_REVIEW','more_evidence':'UNRESOLVED','exclude':'UNRESOLVED'}[payload['decision']]
    corrections=[];refs=[]
    for field,value in payload['fields'].items():
        corrections.append(f"{field}: {value['decision']}; value={value['value']}; reason={value['reason']}")
        if value['reference']:refs.append(f"{field}: {value['reference']} | {value['quote']}")
    row.update(proposed_route=card['route'],human_route=route,
        event_correct_as_written={'supported':'yes','corrected':'no','more_evidence':'uncertain','exclude':'uncertain'}[payload['decision']],
        date_fields_correct='not_separately_scored',correction=safe_cell('\n'.join(corrections)+'\nOverall: '+payload['notes']),
        evidence_reference=safe_cell('\n'.join(refs)),reviewer=safe_cell(payload['reviewer'].strip()),reviewed_at=now,
        review_decision=payload['decision'],reviewed_source_sha256=card['source_sha256'],
        field_reviews_json=json.dumps(payload['fields'],ensure_ascii=False),review_coverage=payload['coverage'],overall_note=safe_cell(payload['notes']))
    # A timestamped backup preserves any assistant/user review that is replaced.
    if old:
        backup=path.parent/'review-backups';backup.mkdir(exist_ok=True)
        (backup/(datetime.now().strftime('%Y%m%dT%H%M%S%f')+'-human-labels.csv')).write_bytes(old)
    tmp=path.with_name(path.name+'.tmp')
    with tmp.open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=columns);writer.writeheader();writer.writerows(rows)
        handle.flush();os.fsync(handle.fileno())
    os.replace(tmp,path)
    with (path.parent/'review-submissions.jsonl').open('a') as handle:
        handle.write(json.dumps({'saved_at':now,'payload':payload},ensure_ascii=False)+'\n')
    return now


def make_handler(pack, labels, token, origin):
    """Close over fixed paths; request data cannot select arbitrary local files."""
    class Handler(BaseHTTPRequestHandler):
        """Serve the minimal review UI and authenticated same-origin submission."""
        def log_message(self,*args):
            """Avoid logging review text or authentication tokens."""
            pass
        def reply(self,status,body,kind='application/json'):
            """Send non-cacheable local content without cross-origin permissions."""
            if not isinstance(body,bytes):body=body.encode()
            self.send_response(status);self.send_header('Content-Type',kind)
            self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
        def valid_host(self):
            """Reject DNS-rebinding Host headers even though the socket is loopback."""
            return self.headers.get('Host')==urlsplit(origin).netloc
        def do_GET(self):
            """Serve only the template, packaged data, labels and allowed PDFs."""
            if not self.valid_host():return self.reply(403,'{}')
            path=urlsplit(self.path).path
            if path=='/':
                page=Path('review_ui/simple.html').read_text().replace('__TOKEN__',token)
                return self.reply(200,page,'text/html; charset=utf-8')
            if path=='/data':
                value={**pack,'labels_path':str(labels.resolve())}
                return self.reply(200,json.dumps(value))
            if path=='/saved':
                rows=list(csv.DictReader(labels.open())) if labels.exists() else []
                return self.reply(200,json.dumps(rows))
            if path=='/pdf':
                ident=parse_qs(urlsplit(self.path).query).get('id',[''])[0]
                card=next((c for c in pack['cards'] if c['id']==ident),None)
                if card and card.get('pdf_path'):
                    return self.reply(200,Path(card['pdf_path']).read_bytes(),'application/pdf')
            return self.reply(404,'{}')
        def do_POST(self):
            """Validate token, origin, body size and content before one atomic save."""
            if not self.valid_host() or self.path!='/submit' or self.headers.get('Origin')!=origin or self.headers.get('X-Review-Token')!=token:
                return self.reply(403,json.dumps({'error':'Submission must come from this local review page.'}))
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=200000:raise ValueError('Submission is too large or empty.')
                payload=json.loads(self.rfile.read(size))
                card=validate_submission(payload,pack['cards'])
                saved=save_submission(labels,card,payload)
                self.reply(200,json.dumps({'saved_at':saved,'path':str(labels.resolve())}))
            except (ValueError,KeyError,TypeError) as exc:
                self.reply(400,json.dumps({'error':str(exc)}))
            except OSError:
                self.reply(500,json.dumps({'error':'Could not save the CSV. Your form remains on screen; check file permissions.'}))
    return Handler


def main():
    """Start one local reviewer session; no internet-facing binding is permitted."""
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pack',type=Path,required=True)
    parser.add_argument('--labels',type=Path,required=True)
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--open-browser',action='store_true')
    args=parser.parse_args()
    if not args.labels.resolve().is_relative_to(Path('runs').resolve()):raise ValueError('Labels must remain under runs/')
    pack=json.loads(args.pack.read_text());origin=f'http://127.0.0.1:{args.port}'
    server=HTTPServer(('127.0.0.1',args.port),make_handler(pack,args.labels,secrets.token_urlsafe(32),origin))
    print(f'Review page: {origin} | saves to {args.labels}',flush=True)
    if args.open_browser:
        import webbrowser
        webbrowser.open(origin)
    server.serve_forever()


if __name__=='__main__':main()
