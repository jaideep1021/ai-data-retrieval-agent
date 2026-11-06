"""Metrics count wrong acceptance and preserve undefined precision."""
import json
from pathlib import Path
import tempfile
import unittest
from evaluate_structured import score_trial,summarize,execute
from tests.test_business_agent import TASK


class StructuredEvaluationTests(unittest.TestCase):
    def test_wrong_acceptance_not_hidden_by_correct_candidate(self):
        result={'input':TASK,'provider':'brave','candidate_source_index':0,
                'sources':[{'value':'123.45','context_match':True,'status':'RETRIEVED'}],
                'accepted_value':'999','authority_policy':'ACCEPT_AUTHORITATIVE_RECORD',
                'agreement_policy':'INSUFFICIENT_EVIDENCE','seconds':1,'requests':[]}
        ref={'expected':'123.45','absolute_tolerance':'0.01','split':'development'}
        row=score_trial(result,ref);summary=summarize([row])['brave']
        self.assertTrue(row['correct']);self.assertFalse(row['accepted_correct'])
        self.assertEqual(summary['incorrect_accepted'],1)
        self.assertEqual(summary['accepted_precision'],0)

    def test_abstention_has_undefined_precision(self):
        result={'input':TASK,'provider':'serpapi','candidate_source_index':None,'sources':[],
                'authority_policy':'UNRESOLVED','agreement_policy':'INSUFFICIENT_EVIDENCE',
                'seconds':1,'requests':[{'kind':'search'}]}
        row=score_trial(result,{'expected':'123','absolute_tolerance':'0','split':'development'})
        summary=summarize([row])['serpapi']
        self.assertEqual(summary['accuracy'],0);self.assertIsNone(summary['accepted_precision'])
        self.assertEqual(summary['search_cost_scenario_usd'],.025)

    def test_holdout_freeze_mismatch_blocks_before_network(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);inputs=root/'inputs.json';freeze=root/'freeze.json'
            inputs.write_text(json.dumps([{**TASK,'record_id':'airfare-07'}]))
            freeze.write_text(json.dumps({'source_hashes':{},'input_sha256':'wrong'}))
            with self.assertRaisesRegex(ValueError,'frozen'):
                execute(inputs,root/'output','evaluation',freeze)
            self.assertFalse((root/'output').exists())


if __name__=='__main__':unittest.main()
