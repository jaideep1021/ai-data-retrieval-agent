"""Offline business retrieval contracts: no credentials or live services needed."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from autonomous import QueryPlan
from business_agent import (BusinessClaim, BusinessInput, BusinessRetriever, assess_claim,
                            compare_sources, decimal_value, evidence_context, number_in_quote, run)
from multisource import SourceSelection
from search_providers import SearchServiceError

TASK = {'record_id': 'synthetic-01', 'city1': 'Alpha, AA', 'city2': 'Beta, BB',
        'citymarketid_1': '30001', 'citymarketid_2': '30002', 'year': 2024,
        'quarter': 4, 'attribute': 'fare', 'unit': 'USD', 'question': 'Historical fare?',
        'condition': 'missing', 'current_value': None}
TEXT = 'Alpha, AA / Beta, BB | 2024 Q4 | average each-way market fare USD | 123.45'
CLAIM = dict(value='123.45', value_quote='123.45', city1='Alpha, AA', city2='Beta, BB',
             market_quote='Alpha, AA / Beta, BB', year=2024, quarter=4, period_quote='2024 Q4',
             attribute='fare', unit='USD', definition_quote='average each-way market fare USD')


class GroundingTests(unittest.TestCase):
    def test_reference_fields_rejected(self):
        for key in ('expected', 'source_url', 'absolute_tolerance', 'dataset_id'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                BusinessInput.model_validate({**TASK, key: 'hidden'})

    def test_decimal_and_whole_token_matching(self):
        self.assertTrue(number_in_quote('1234.50', 'USD 1,234.50 per trip'))
        for text in ('11234.50', '1234.501', '-1234.50', 'x1234.50'):
            self.assertFalse(number_in_quote('1234.50', text))
        for value in ('NaN', 'Infinity', '-2', '1e2', '1,00'):
            with self.assertRaises(ValueError): decimal_value(value)

    def test_correct_context_and_wrong_period(self):
        self.assertTrue(assess_claim(BusinessClaim(**CLAIM), TEXT, TASK)['context_match'])
        result = assess_claim(BusinessClaim(**{**CLAIM, 'quarter': 3}), TEXT, TASK)
        self.assertTrue(result['numeric_grounded'])
        self.assertFalse(result['context_match'])
        self.assertIn('PERIOD_MISMATCH_OR_MISSING', result['failure_labels'])

    def test_missing_quote_wrong_market_and_unit(self):
        for update in ({'market_quote': None}, {'city2': 'Other'}, {'unit': 'USD/ticket'},
                       {'definition_quote': 'invented text'}, {'value_quote': '123.450'}):
            with self.subTest(update=update):
                self.assertFalse(assess_claim(BusinessClaim(**{**CLAIM, **update}), TEXT, TASK)['context_match'])

    def test_context_selection_uses_question_not_current_value(self):
        text = 'header ' + 'x'*25000 + ' Alpha, AA 30001 record ' + 'y'*25000
        a, offsets = evidence_context(text, TASK)
        b, _ = evidence_context(text, {**TASK, 'current_value': 'secret-decoy'})
        self.assertEqual(a, b)
        self.assertIn('30001', a)
        self.assertLessEqual(sum(end-start for start, end in offsets), 24000)

    def test_duplicate_conflict_and_agreement(self):
        first = {'context_match': True, 'claim': CLAIM, 'sha256': 'one'}
        second = {**first, 'sha256': 'two'}
        self.assertEqual(compare_sources([first])['decision'], 'INSUFFICIENT_EVIDENCE')
        self.assertEqual(compare_sources([first, first])['decision'], 'DUPLICATE_EVIDENCE')
        self.assertEqual(compare_sources([first, second])['decision'], 'AGREEMENT_OBSERVED')
        second = {**second, 'claim': {**CLAIM, 'value': '123.46'}}
        self.assertEqual(compare_sources([first, second])['decision'], 'CONFLICT')


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.fetcher = BusinessRetriever()
        self.addCleanup(self.fetcher.session.close)

    def test_json_keeps_precision(self):
        raw = '[{"amount":123.456789012345678901}]'
        with patch.object(self.fetcher, 'read', return_value=(200, 'application/json', raw, 'https://example.org/data')):
            self.assertEqual(self.fetcher.fetch_document('https://example.org/data')['text'], raw)

    def test_html_links_are_literal_and_no_script_evidence(self):
        raw = '<main>Data <a href="/data.csv">Download</a><script>secret</script></main>'
        with patch.object(self.fetcher, 'read', return_value=(200, 'text/html', raw, 'https://example.org/page')):
            result = self.fetcher.fetch_document('https://example.org/page')
            self.assertEqual(result['links'][0]['url'], 'https://example.org/data.csv')
            self.assertNotIn('secret', result['text'])

    def test_content_links_survive_large_navigation_and_keep_https_policy(self):
        nav = '<nav>' + ''.join(f'<a href="/data/{i}">Data</a>' for i in range(510)) + '</nav>'
        raw = nav + '<main><a href="/agreements">Agreements</a><a href="http://old.example/a">Old</a><a href="#top">Self</a><a href="/agreements#part">Duplicate</a></main>'
        with patch.object(self.fetcher, 'read', return_value=(200, 'text/html', raw, 'https://example.org/page')):
            links = self.fetcher.fetch_document('https://example.org/page')['links']
        self.assertEqual(links[0]['url'], 'https://example.org/agreements')
        self.assertEqual(len(links), 40)
        self.assertEqual(len({x['url'] for x in links}), 40)
        self.assertTrue(all(x['url'].startswith('https://') for x in links))
        self.assertNotIn('https://example.org/page', [x['url'] for x in links])

    def test_navigation_inside_main_does_not_outrank_article(self):
        raw = '<main><nav><a href="/menu.pdf">Menu</a></nav><a href="/agreement">Agreement</a><a href="/instrument.pdf">Instrument</a></main>'
        with patch.object(self.fetcher, 'read', return_value=(200, 'text/html', raw, 'https://example.org/page')):
            links = self.fetcher.fetch_document('https://example.org/page')['links']
        self.assertEqual([x['title'] for x in links], ['Instrument', 'Agreement', 'Menu'])

    def test_unsupported_and_bad_responses(self):
        for response in [(403, 'text/html', 'Denied', 'https://example.org'),
                         (200, 'application/pdf', 'pdf', 'https://example.org'),
                         (200, 'application/json', 'broken', 'https://example.org')]:
            with patch.object(self.fetcher, 'read', return_value=response), self.assertRaises(ValueError):
                self.fetcher.fetch_document('https://example.org')


class RunTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / 'trial'
        self.provider = Mock(name='provider')
        self.provider.name = 'brave'
        self.provider.search.return_value = [{'url': 'https://example.org/page', 'title': 'Data', 'snippet': ''}]
        self.fetcher = Mock(policy_events=[])
        self.fetcher.fetch_document.return_value = {'text': TEXT, 'final_url': 'https://example.org/page',
            'content_type': 'text/html', 'raw_sha256': 'raw', 'links': []}
        self.model = Mock()
        self.model.ask.side_effect = [QueryPlan(query='Alpha Beta historical fare 2024 Q4'),
            SourceSelection(candidate_indices=[0], reason='Data'), BusinessClaim(**CLAIM),
            QueryPlan(query='Alpha Beta 2024 Q4 average market fare')]

    def run_trial(self):
        return run(TASK, self.model, self.provider, self.fetcher, self.output)

    def test_single_source_preserved_but_not_accepted(self):
        result = self.run_trial()
        self.assertEqual(result['decision'], 'INSUFFICIENT_EVIDENCE')
        self.assertEqual(result['candidate_source_id'], 0)
        self.assertTrue(result['sources'][0]['context_match'])
        self.assertTrue((self.output / result['sources'][0]['evidence_file']).exists())
        self.assertEqual(json.loads((self.output / 'result.json').read_text())['reference_used'], False)
        for call in self.model.ask.call_args_list:
            prompt_data = json.dumps(call.args[2])
            for forbidden in ('expected', 'answer-key', 'evaluator-manifest', '4f3n-jbg2'):
                self.assertNotIn(forbidden, prompt_data)

    def test_quota_stops_without_leaking_exception(self):
        self.provider.search.side_effect = SearchServiceError(429)
        result = self.run_trial()
        self.assertTrue(result['stop_batch'])
        self.assertEqual(self.provider.search.call_count, 1)
        self.fetcher.fetch_document.assert_not_called()

    def test_model_quota_during_extraction_stops(self):
        error = RuntimeError('private-key')
        error.code = 429
        self.model.ask.side_effect = [QueryPlan(query='Alpha Beta 2024 Q4'),
            SourceSelection(candidate_indices=[0], reason='Data'), error]
        result = self.run_trial()
        self.assertTrue(result['stop_batch'])
        self.assertNotIn('private-key', (self.output / 'result.json').read_text())

    def test_fetch_error_is_recorded(self):
        self.fetcher.fetch_document.side_effect = ValueError('secret-key')
        self.model.ask.side_effect = [QueryPlan(query='Alpha Beta 2024 Q4'),
            SourceSelection(candidate_indices=[0], reason='Data'), QueryPlan(query='Alpha Beta historical fare')]
        result = self.run_trial()
        self.assertEqual(result['sources'][0]['status'], 'ERROR')
        self.assertIsNone(result['candidate_source_id'])
        self.assertNotIn('secret-key', (self.output / 'result.json').read_text())

    def test_invented_domain_and_invalid_selection(self):
        self.model.ask.side_effect = [QueryPlan(query='site:invented.example fare')]
        self.assertEqual(self.run_trial()['decision'], 'ERROR')
        self.provider.search.assert_not_called()

    def test_existing_evidence_never_overwritten(self):
        self.output.mkdir()
        with self.assertRaises(FileExistsError): self.run_trial()

    def test_link_discovery_chain(self):
        self.fetcher.fetch_document.side_effect = [
            {'text': 'Dataset catalogue', 'final_url': 'https://example.org/page', 'content_type': 'text/html',
             'raw_sha256': 'raw', 'links': [{'url': 'https://example.org/data.csv', 'title': 'CSV', 'snippet': ''}]},
            {'text': TEXT, 'final_url': 'https://example.org/data.csv', 'content_type': 'text/csv', 'raw_sha256': 'raw2', 'links': []}]
        empty = {key: None for key in CLAIM}
        self.model.ask.side_effect = [QueryPlan(query='Alpha Beta fare 2024 Q4'),
            SourceSelection(candidate_indices=[0], reason='Catalog'), BusinessClaim(**empty),
            SourceSelection(candidate_indices=[0], reason='Linked data'), BusinessClaim(**CLAIM),
            QueryPlan(query='Alpha Beta historical market fare')]
        result = self.run_trial()
        self.assertEqual(result['sources'][1]['discovery_parent'], 'https://example.org/page')
        self.assertEqual(result['candidate_source_id'], 1)


if __name__ == '__main__':
    unittest.main()
