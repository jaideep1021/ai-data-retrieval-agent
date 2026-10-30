"""Metric correctness, denominators and no answer-based candidate selection."""
import unittest
from unittest.mock import Mock
import evaluate as ev


class EvaluationTests(unittest.TestCase):
    def test_error_counts_in_accuracy_denominator(self):
        rows=[]
        for result in [{'retrieved_value':'Final','evidence_valid':True,'evidence_file':'file','decision':'ACCEPT'},
                       {'decision':'ERROR'}]:
            rows.append({'config':'baseline',**ev.score('baseline',result,'Final'),'seconds':1,
                         'cost':ev.usage_cost([],1,'serpapi','gemini-3.5-flash-lite')})
        summary=ev.summarize(rows)['baseline']
        self.assertEqual(summary['accuracy'],.5)
        self.assertEqual(summary['retrieval_success_rate'],.5)
        self.assertEqual(summary['accepted_precision'],1)

    def test_first_candidate_not_oracle_selected(self):
        result={'decision':'CONFLICT','sources':[
            {'status':'GROUNDED','claim':{'value':'Wrong'},'evidence_file':'a'},
            {'status':'GROUNDED','claim':{'value':'Right'},'evidence_file':'b'}]}
        scored=ev.score('autonomous_brave',result,'Right')
        self.assertFalse(scored['correct'])
        self.assertFalse(scored['accepted'])
        self.assertEqual(scored['candidate'],'Wrong')
        self.assertTrue(scored['retrieved'])

    def test_correct_single_source_is_not_accepted(self):
        result={'decision':'INSUFFICIENT_EVIDENCE','sources':[
            {'status':'GROUNDED','claim':{'value':'Final'},'evidence_file':'a'}]}
        scored=ev.score('autonomous_serpapi',result,'Final')
        self.assertTrue(scored['correct'])
        self.assertFalse(scored['accepted_correct'])

    def test_cost_caching_thinking_and_missing_usage(self):
        calls=[{'usage':{'prompt_token_count':1000,'cached_content_token_count':100,
                        'candidates_token_count':50,'thoughts_token_count':50}}, {'status':'error'}]
        cost=ev.usage_cost(calls,2,'brave','gemini-3.5-flash-lite')
        self.assertAlmostEqual(cost['gemini_estimated_usd'],.000523)
        self.assertFalse(cost['usage_complete'])
        self.assertEqual(cost['search_scenario_usd'],.01)
        self.assertIsNone(ev.usage_cost(calls,2,'brave','other')['total_scenario_usd'])

    def test_metering_preserves_sdk_arguments_and_hides_errors(self):
        client=Mock()
        client.generate_content.side_effect=RuntimeError('private-key')
        meter=ev.MeteredModels(client)
        with self.assertRaises(RuntimeError):
            meter.generate_content(model='test',contents='data')
        client.generate_content.assert_called_once_with(model='test',contents='data')
        self.assertNotIn('private-key',str(meter.calls))

    def test_rate_limit_stops_subsequent_model_requests(self):
        client=Mock()
        error=RuntimeError('private quota details')
        error.code=429
        client.generate_content.side_effect=error
        pacing={'interval':0,'last':0,'rate_limited':False}
        meter=ev.MeteredModels(client,pacing)
        with self.assertRaises(RuntimeError):
            meter.generate_content(model='test')
        with self.assertRaises(ev.RateLimitStop):
            meter.generate_content(model='test')
        self.assertEqual(client.generate_content.call_count,1)
        self.assertEqual(meter.calls[0]['http_status'],429)

    def test_zero_acceptances_is_undefined_precision(self):
        row={'config':'baseline',**ev.score('baseline',{'decision':'ERROR'},'Final'),'seconds':0,
             'cost':ev.usage_cost([],0,'serpapi','gemini-3.5-flash-lite')}
        self.assertIsNone(ev.summarize([row])['baseline']['accepted_precision'])


if __name__=='__main__':
    unittest.main()
