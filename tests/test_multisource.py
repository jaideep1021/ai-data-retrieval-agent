"""Deterministic contracts and failure paths; no live API calls."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, MagicMock, patch

from autonomous import Claim, QueryPlan
import multisource as multi
from search_providers import SearchProvider


class MultiSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / 'run'
        self.provider = Mock()
        self.provider.name = 'serpapi'
        self.provider.search.return_value = [
            {'url': 'https://one.example/doc', 'title': 'Document', 'snippet': 'untrusted'},
            {'url': 'https://two.example/doc', 'title': 'Document', 'snippet': 'untrusted'}]
        self.model = Mock(model='fake', calls=[])
        self.claim = Claim(value='Example title', evidence_quote='Title: Example title', entity_quote='PEP: 703')
        self.model.ask.side_effect = [QueryPlan(query='PEP 703 title'),
                                     multi.SourceSelection(candidate_indices=[0, 1], reason='Relevant'),
                                     self.claim, self.claim]
        self.fetcher = Mock(policy_events=[])
        self.fetcher.fetch.side_effect = [
            ('PEP: 703\nTitle: Example title\nPublisher A', 'https://one.example/doc'),
            ('PEP: 703\nTitle: Example title\nPublisher B', 'https://two.example/doc')]

    def run_case(self):
        return multi.run('PEP 703', 'title', self.model, [self.provider], self.fetcher, self.output, 2)

    def test_agreement_and_provenance_not_truth(self):
        result = self.run_case()
        self.assertEqual(result['decision'], 'AGREEMENT_OBSERVED')
        self.assertFalse(result['verified_truth'])
        self.assertEqual(result['independence'], 'NOT_ESTABLISHED')
        self.assertFalse(result['reference_used'])
        for source in result['sources']:
            self.assertTrue((self.output / source['evidence_file']).exists())
            self.assertEqual(len(source['sha256']), 64)
        self.assertEqual(json.loads((self.output / 'result.json').read_text())['decision'], result['decision'])
        for call in self.model.ask.call_args_list[2:]:
            self.assertEqual(set(call.args[2]), {'entity', 'attribute', 'page_text'})

    def test_conflict_retains_both_claims(self):
        other = Claim(value='Different title', evidence_quote='Title: Different title', entity_quote='PEP: 703')
        self.model.ask.side_effect = [QueryPlan(query='PEP 703 title'),
                                    multi.SourceSelection(candidate_indices=[0, 1], reason='Relevant'), self.claim, other]
        self.fetcher.fetch.side_effect = [('PEP: 703\nTitle: Example title', 'https://one.example/doc'),
                                         ('PEP: 703\nTitle: Different title', 'https://two.example/doc')]
        result = self.run_case()
        self.assertEqual(result['decision'], 'CONFLICT')
        self.assertEqual(len(result['value_groups']), 2)

    def test_identical_text_is_not_corroboration(self):
        self.fetcher.fetch.side_effect = [('PEP: 703\nTitle: Example title', 'https://one.example/doc'),
                                         ('PEP: 703\nTitle: Example title', 'https://two.example/doc')]
        self.assertEqual(self.run_case()['decision'], 'DUPLICATE_EVIDENCE')

    def test_redirects_to_same_page_do_not_count_twice(self):
        self.fetcher.fetch.side_effect = [('PEP: 703\nTitle: Example title', 'https://one.example/doc')]*2
        result = self.run_case()
        self.assertEqual(result['decision'], 'INSUFFICIENT_EVIDENCE')
        self.assertEqual(result['sources'][1]['status'], 'DUPLICATE_URL')
        self.assertEqual(self.model.ask.call_count, 3)

    def test_source_failure_preserves_other_evidence_without_secret(self):
        self.fetcher.fetch.side_effect = [('PEP: 703\nTitle: Example title', 'https://one.example/doc'),
                                         RuntimeError('secret-token')]
        result = self.run_case()
        self.assertEqual(result['decision'], 'INSUFFICIENT_EVIDENCE')
        self.assertEqual(result['grounded_sources'], 1)
        self.assertNotIn('secret-token', (self.output / 'result.json').read_text())

    def test_ungrounded_claim_does_not_create_conflict(self):
        self.fetcher.fetch.side_effect = [('PEP: 703\nTitle: Example title', 'https://one.example/doc'),
                                         ('PEP: 703\nNo title here', 'https://two.example/doc')]
        result = self.run_case()
        self.assertEqual(result['decision'], 'INSUFFICIENT_EVIDENCE')
        self.assertEqual(result['sources'][1]['status'], 'UNSUPPORTED')

    def test_invalid_selection_does_not_fetch(self):
        for indices in ([0, 0], [0, 8], [-1]):
            with self.subTest(indices=indices):
                self.output = Path(self.temp.name) / str(indices)
                self.model.ask.side_effect = [QueryPlan(query='PEP 703 title'),
                    multi.SourceSelection(candidate_indices=indices, reason='Bad selection')]
                self.assertEqual(self.run_case()['decision'], 'ERROR')
        self.fetcher.fetch.assert_not_called()

    def test_all_searches_fail_error_is_recorded_and_bounded(self):
        self.provider.search.side_effect = TimeoutError('secret-token')
        self.model.ask.side_effect = [QueryPlan(query='PEP 703 title'), QueryPlan(query='PEP 703 original title')]
        result = self.run_case()
        self.assertEqual(result['decision'], 'ERROR')
        self.assertEqual(self.provider.search.call_count, 2)
        self.assertNotIn('secret-token', (self.output / 'result.json').read_text())

    def test_empty_search_abstains(self):
        self.provider.search.return_value = []
        self.model.ask.side_effect = [QueryPlan(query='PEP 703 title'), QueryPlan(query='PEP 703 original title')]
        self.assertEqual(self.run_case()['decision'], 'INSUFFICIENT_EVIDENCE')
        self.fetcher.fetch.assert_not_called()

    def test_second_provider_can_succeed_after_first_fails(self):
        failed = Mock(name='failed')
        failed.name = 'brave'
        failed.search.side_effect = TimeoutError('private')
        result = multi.run('PEP 703', 'title', self.model, [failed, self.provider], self.fetcher, self.output, 2)
        self.assertEqual(result['decision'], 'AGREEMENT_OBSERVED')
        self.assertEqual([a['status'] for a in result['search_attempts']], ['error', 'ok'])

    def test_existing_output_is_preserved(self):
        self.output.mkdir()
        with self.assertRaises(FileExistsError):
            self.run_case()


class ProviderTests(unittest.TestCase):
    def test_serpapi_normalization(self):
        client = Mock()
        client.search.return_value = {'organic_results': [{'link': 'https://example.org', 'snippet': 'text'}]}
        result = SearchProvider('serpapi', client=client).search('query')
        self.assertEqual(result[0]['url'], 'https://example.org')
        client.search.assert_called_once_with(engine='google', q='query', num=10)

    def test_serpapi_error(self):
        client = Mock()
        client.search.return_value = {'error': 'private'}
        with self.assertRaises(ValueError):
            SearchProvider('serpapi', client=client).search('query')

    @patch('search_providers.requests.get')
    def test_brave_contract_and_no_redirects(self, get):
        response = MagicMock(status_code=200)
        response.json.return_value = {'web': {'results': [{'url': 'https://example.org', 'description': 'text'}]}}
        get.return_value.__enter__.return_value = response
        result = SearchProvider('brave', key='test-only').search('query')
        self.assertEqual(result[0]['snippet'], 'text')
        self.assertFalse(get.call_args.kwargs['allow_redirects'])
        self.assertEqual(get.call_args.kwargs['headers']['X-Subscription-Token'], 'test-only')
        self.assertEqual(get.call_args.kwargs['params'], {'q': 'query', 'count': 10})

    @patch('search_providers.requests.get')
    def test_brave_failure_statuses(self, get):
        for status in (301, 401, 403, 429, 500):
            get.return_value.__enter__.return_value = MagicMock(status_code=status)
            with self.subTest(status=status), self.assertRaises(ValueError):
                SearchProvider('brave', key='test-only').search('query')

    @patch('search_providers.requests.get')
    def test_brave_malformed_json(self, get):
        response = MagicMock(status_code=200)
        response.json.side_effect = ValueError('Invalid JSON')
        get.return_value.__enter__.return_value = response
        with self.assertRaises(ValueError):
            SearchProvider('brave', key='test-only').search('query')

    def test_unknown_provider_and_missing_credentials(self):
        for name in ('unknown', 'serpapi', 'brave'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                SearchProvider(name)


if __name__ == '__main__':
    unittest.main()
