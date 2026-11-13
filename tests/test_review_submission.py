"""Validate persistence and routing without touching the user's real labels."""
import csv
import tempfile
import unittest
from pathlib import Path
from aviation_review_server import validate_submission,save_submission
from aviation_attachments import discover_attachments


class SubmissionTests(unittest.TestCase):
    def setUp(self):
        self.card={'id':'case','source_sha256':'hash','route':'NEEDS_REVIEW','items':[{'id':'status'}]}
        self.payload={'candidate_id':'case','source_sha256':'hash','reviewer':'Researcher',
         'notes':'Need final source','coverage':'passages','decision':'more_evidence',
         'fields':{'status':{'decision':'unknown','value':'','reference':'','quote':'','reason':'Missing final status'}}}

    def test_missing_evidence_cannot_be_correction(self):
        self.payload['fields']['status']['decision']='correct'
        with self.assertRaises(ValueError):validate_submission(self.payload,[self.card])

    def test_unknown_not_supported(self):
        self.payload['decision']='supported'
        with self.assertRaises(ValueError):validate_submission(self.payload,[self.card])

    def test_changed_source_rejected(self):
        self.payload['source_sha256']='old'
        with self.assertRaises(ValueError):validate_submission(self.payload,[self.card])

    def test_save_preserves_other_rows_and_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'human-labels.csv'
            p.write_text('candidate_id,reviewer\nother,Original reviewer\n')
            validate_submission(self.payload,[self.card]);save_submission(p,self.card,self.payload)
            with p.open() as handle: rows=list(csv.DictReader(handle))
            self.assertEqual(rows[0]['reviewer'],'Original reviewer')
            self.assertEqual(rows[1]['human_route'],'UNRESOLVED')
            self.assertEqual(rows[1]['reviewer'],'Researcher')
            self.assertTrue(list((p.parent/'review-backups').glob('*.csv')))
            self.assertEqual(len((p.parent/'review-submissions.jsonl').read_text().splitlines()),1)

    def test_actual_links_only_and_license_excluded(self):
        html='<div>Name: report.pdf <a href="/bitstreams/abc/download">Download</a></div><div>Name: license.txt <a href="/bitstreams/xyz/download">Download</a></div>'
        rows=discover_attachments(html,'https://example.org/item')
        self.assertEqual([r['url'] for r in rows],['https://example.org/bitstreams/abc/download'])

    def test_correction_with_evidence_and_formula_safe_name(self):
        self.payload.update(decision='corrected',reviewer='=malicious_formula')
        self.payload['fields']['status'].update(decision='correct',value='draft-indicated',
            reference='https://example.org p.1',quote='Draft for consultation')
        validate_submission(self.payload,[self.card])
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'human-labels.csv';save_submission(p,self.card,self.payload)
            with p.open() as handle:row=next(csv.DictReader(handle))
            self.assertTrue(row['reviewer'].startswith("'="))
            self.assertEqual(row['review_decision'],'corrected')

    def test_fallback_uses_observed_title_and_official_result(self):
        from aviation_attachments import fallback_query,official_pdf_results
        query=fallback_query({'label':'Name: Example Regulations 2018.pdf Size: 15 MB'})
        self.assertEqual(query,'Example Regulations 2018 official PDF')
        rows=[{'url':'https://www.kcaa.or.ke/doc.pdf'}, {'url':'https://kcaa.or.ke.evil.example/doc.pdf'}]
        self.assertEqual(official_pdf_results(rows),rows[:1])
