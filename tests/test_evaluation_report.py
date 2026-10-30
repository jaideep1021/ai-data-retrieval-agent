"""Public report excludes raw runtime payloads and labels incomplete experiments."""
import json
from pathlib import Path
import tempfile
import unittest

import evaluate
from evaluation_report import build


class ReportTests(unittest.TestCase):
    def test_partial_run_is_labelled_and_raw_payload_excluded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            run=root/'run'
            trial=run/'obs-01-baseline'
            trial.mkdir(parents=True)
            detail={'decision':'ERROR','error_stage':'extraction',
                    'raw_payload':'PRIVATE_RUNTIME_TEXT'}
            (trial/'result.json').write_text(json.dumps(detail))
            row={'id':'obs-01','pep_number':202,'attribute':'title','expected':'Example',
                 'config':'baseline','artifact':trial.name,'seconds':1,
                 'cost':evaluate.usage_cost([],1,'serpapi','gemini-3.5-flash-lite'),
                 **evaluate.score('baseline',detail,'Example')}
            (run/'observations.json').write_text(json.dumps([row]))
            (run/'manifest.json').write_text('{}')
            build(run,root/'report')
            text=(root/'report'/'evaluation-step3-findings.md').read_text()
            self.assertIn('**1/60**',text)
            self.assertIn('Completion recorded: **no**',text)
            self.assertIn('run error: extraction',text)
            exported=(root/'report'/'evaluation-results.json').read_text()
            self.assertNotIn('PRIVATE_RUNTIME_TEXT',exported)
            self.assertEqual(json.loads(exported)['summary']['baseline']['accuracy'],0)


if __name__=='__main__':
    unittest.main()
