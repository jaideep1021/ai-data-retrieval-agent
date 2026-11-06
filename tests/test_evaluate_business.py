"""Scoring must distinguish retrieval, contextual correctness and acceptance."""
import unittest
from unittest.mock import Mock, patch

from evaluate_business import PacedModels, score_trial, summarize, usage_estimate


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.reference = {'expected': '100.005', 'absolute_tolerance': '0.01', 'split': 'development'}
        self.result = {'input': {'record_id': 'synthetic', 'condition': 'missing', 'attribute': 'fare'},
                       'provider': 'brave', 'candidate_source_id': 0,
                       'sources': [{'id': 0, 'claim': {'value': '100.00'}, 'context_match': True,
                                    'evidence_file': 'evidence.txt'}],
                       'decision': 'INSUFFICIENT_EVIDENCE', 'seconds': 1, 'search_attempts': []}

    def test_correct_retrieval_can_be_unaccepted(self):
        row = score_trial(self.result, self.reference)
        self.assertTrue(row['context_correct'])
        self.assertTrue(row['retrieved'])
        self.assertFalse(row['accepted'])

    def test_wrong_period_is_not_contextually_correct(self):
        self.result['sources'][0]['context_match'] = False
        row = score_trial(self.result, self.reference)
        self.assertTrue(row['numeric_correct'])
        self.assertFalse(row['context_correct'])

    def test_first_candidate_not_cherry_picked(self):
        self.result['sources'][0]['claim']['value'] = '999'
        self.result['sources'].append({'id': 1, 'claim': {'value': '100.005'}, 'context_match': True})
        self.assertFalse(score_trial(self.result, self.reference)['context_correct'])

    def test_actual_accepted_value_scored_separately(self):
        self.result.update(decision='AGREEMENT_OBSERVED', accepted_value='999')
        row = score_trial(self.result, self.reference)
        self.assertTrue(row['context_correct'])
        self.assertTrue(row['incorrect_accepted'])

    def test_absent_candidate_and_zero_acceptance(self):
        self.result.update(candidate_source_id=None, sources=[])
        row = score_trial(self.result, self.reference)
        row['usage'] = {'estimated_usd': None}
        group = summarize([row])['provider']['brave']
        self.assertEqual(group['accuracy'], 0)
        self.assertEqual(group['unresolved_rate'], 1)
        self.assertIsNone(group['accepted_precision'])
        self.assertIsNone(group['cost_per_correct_accepted'])

    def test_no_prices_or_missing_usage_is_not_zero_cost(self):
        self.assertIsNone(usage_estimate([], 1, 'brave', {})['estimated_usd'])
        rates = dict(brave_per_search=.005, model_input_per_million=.3,
                     model_cached_per_million=.03, model_output_per_million=2.5)
        self.assertIsNone(usage_estimate([{'status': 'error'}], 1, 'brave', rates)['estimated_usd'])
        cost = usage_estimate([{'usage': {'prompt_token_count': 1000, 'candidates_token_count': 100}}], 1, 'brave', rates)
        self.assertAlmostEqual(cost['estimated_usd'], .00555)
        self.assertFalse(cost['billing_verified'])

    @patch('evaluate_business.time.sleep')
    @patch('evaluate_business.time.perf_counter', return_value=10)
    def test_shared_pacing_and_output_limit(self, clock, sleep):
        models = Mock()
        models.generate_content.return_value.usage_metadata = None
        wrapper = PacedModels(models)
        for _ in range(2): wrapper.generate_content(model='mock', config={})
        sleep.assert_called_once_with(7)
        self.assertEqual(models.generate_content.call_args.kwargs['config']['max_output_tokens'], 2048)

class RunnerBoundaryTests(unittest.TestCase):
    """Exercise batch persistence and the no-reference runtime boundary offline."""
    def test_paired_order_and_no_reference_reads(self):
        import json
        import tempfile
        from pathlib import Path
        from evaluate_business import execute
        from tests.test_business_agent import TASK
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inputs = root / 'inputs.json'
            tasks = [{**TASK, 'record_id': f'synthetic-{i}'} for i in range(2)]
            inputs.write_text(json.dumps(tasks))
            order = []
            def trial(task, model, provider, fetcher, folder):
                folder.mkdir()
                result = {'stop_batch': False, 'decision': 'INSUFFICIENT_EVIDENCE'}
                (folder/'result.json').write_text(json.dumps(result))
                order.append((task['record_id'], provider.name))
                return result
            # Real reference files are not even permitted to be opened in run().
            original = Path.read_text
            def guarded(path, *args, **kwargs):
                self.assertNotIn('evaluator-manifest', str(path))
                self.assertNotIn('answer-key', str(path))
                return original(path, *args, **kwargs)
            with patch('evaluate_business.load_dotenv'), patch.dict('os.environ',
                {'GEMINI_API_KEY': 'synthetic', 'SERPAPI_KEY': 'synthetic', 'BRAVE_SEARCH_API_KEY': 'synthetic'}), \
                patch('evaluate_business.genai.Client'), patch('evaluate_business.serpapi.Client'), \
                patch('evaluate_business.SearchProvider') as factory, \
                patch('evaluate_business.BusinessRetriever'), patch('evaluate_business.run', side_effect=trial), \
                patch.object(Path, 'read_text', guarded):
                factory.side_effect = lambda name, **kwargs: type('Provider', (), {'name': name})()
                execute(inputs, root/'output', ['serpapi', 'brave'], [t['record_id'] for t in tasks])
            self.assertEqual(order, [('synthetic-0', 'serpapi'), ('synthetic-0', 'brave'),
                                     ('synthetic-1', 'brave'), ('synthetic-1', 'serpapi')])
            manifest = json.loads((root/'output'/'manifest.json').read_text())
            self.assertEqual(manifest['status'], 'COMPLETE')
            self.assertEqual(manifest['completed_trials'], 4)


if __name__ == '__main__':
    unittest.main()
