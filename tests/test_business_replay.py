"""An offline replay must preserve evidence and errors without using answers."""
import json
from pathlib import Path
import tempfile
import unittest

from replay_business_validation import replay
from tests.test_business_agent import TASK, CLAIM, TEXT


class ReplayTests(unittest.TestCase):
    def test_grouped_claim_replayed_without_overwriting_original(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source'; trial=source/'trial'; trial.mkdir(parents=True)
            text=TEXT.replace('123.45','1,000')
            (trial/'evidence.txt').write_text(text)
            result={'version':'old','input':TASK,'decision':'ERROR','provider':'brave',
                    'candidate_source_id':None,'sources':[{'id':0,'status':'UNSUPPORTED',
                    'numeric_grounded':False,'context_match':False,'sha256':'example',
                    'evidence_file':'evidence.txt','context_offsets':[[0,len(text)]],
                    'claim':{**CLAIM,'value':'1,000','value_quote':'1,000'}}]}
            original=json.dumps(result);(trial/'result.json').write_text(original)
            (source/'manifest.json').write_text(json.dumps({'status':'COMPLETE','version':'old','artifacts':['trial']}))
            replay(source,Path(folder)/'replay')
            after=json.loads((Path(folder)/'replay/trial/result.json').read_text())
            self.assertEqual(after['decision'],'ERROR')
            self.assertEqual(after['candidate_source_id'],0)
            self.assertTrue(after['sources'][0]['numeric_grounded'])
            self.assertEqual((trial/'result.json').read_text(),original)
            manifest=json.loads((Path(folder)/'replay/manifest.json').read_text())
            self.assertEqual(manifest['incremental_model_calls'],0)
            self.assertTrue(manifest['reused_acquisition_time_and_usage'])

    def test_partial_run_not_mislabelled_as_complete_replay(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source'; source.mkdir()
            (source/'manifest.json').write_text(json.dumps({'status':'INTERRUPTED'}))
            with self.assertRaises(ValueError):replay(source,Path(folder)/'out')


if __name__=='__main__':unittest.main()
