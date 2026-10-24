"""Offline contract tests: no API keys, network, browser download or paid calls."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import agent


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.evidence = self.root / 'page.txt'
        self.evidence.write_text('Status: Active', encoding='utf-8')
        self.row = dict(pep_number='8', attribute='status', current_value='Draft')
        self.reference = {'8': {'status': 'Active'}}
        self.stdout = contextlib.redirect_stdout(io.StringIO())
        self.stdout.__enter__()
        self.addCleanup(self.stdout.__exit__, None, None, None)

    def test_official_url_exact_host_path_and_scheme(self):
        self.assertTrue(agent.is_official_pep_url('https://peps.python.org/pep-0008/', 8))
        for url in ['http://peps.python.org/pep-0008/',
                    'https://peps.python.org.evil.test/pep-0008/',
                    'https://peps.python.org@evil.test/pep-0008/',
                    'https://peps.python.org/pep-0020/']:
            self.assertFalse(agent.is_official_pep_url(url, 8))

    def test_verification_decisions(self):
        cases = [('Active', 'Status: Active', 'Draft', 'ACCEPT'),
                 (' active ', 'Status: Active', 'ACTIVE', 'NO_CHANGE'),
                 ('Draft', 'Status: Active', '', 'REVIEW'),
                 ('Active', 'invented quote', '', 'REVIEW'),
                 (None, None, '', 'REVIEW')]
        for value, quote, original, expected in cases:
            with self.subTest(expected=expected, value=value):
                result = agent.verify_extraction(value, quote, 'Status:\n Active', 'Active', original)
                self.assertEqual(result['decision'], expected)

    def test_search_and_fallback(self):
        client = Mock()
        client.search.return_value = {'organic_results': [{'link': agent.canonical_pep_url(8)}]}
        self.assertEqual(agent.discover_source(8, client)['method'], 'serpapi')
        for response in [{}, {'error': 'quota'}]:
            client.search.return_value = response
            self.assertEqual(agent.discover_source(8, client)['method'], 'canonical_fallback')
        client.search.side_effect = RuntimeError('secret-in-sdk-error')
        result = agent.discover_source(8, client)
        self.assertNotIn('secret-in-sdk-error', result['search_issue'])

    def test_bad_rows_become_error_results(self):
        for row in [dict(self.row, pep_number='bad'), dict(self.row, pep_number='-1'),
                    dict(self.row, attribute='unknown'), dict(self.row, pep_number='999'), {}]:
            result = agent.process_record(row, None, self.reference, None, None)
            self.assertEqual(result['decision'], 'ERROR')
            self.assertEqual(result['error_stage'], 'validation')

    def test_process_success_and_extraction_failure(self):
        with patch.object(agent, 'discover_source', return_value=dict(url=agent.canonical_pep_url(8), query='PEP 8', method='serpapi', search_issue='')), \
             patch.object(agent, 'fetch_source', return_value=('Status: Active', agent.canonical_pep_url(8), str(self.evidence))), \
             patch.object(agent, 'extract_attribute') as extract:
            extract.return_value = agent.Extraction(value='Active', evidence_quote='Status: Active')
            result = agent.process_record(self.row, None, self.reference, None, None)
            self.assertEqual(result['decision'], 'ACCEPT')
            self.assertEqual(len(result['evidence_sha256']), 64)
            extract.side_effect = RuntimeError('secret-in-error')
            result = agent.process_record(self.row, None, self.reference, None, None)
            self.assertEqual(result['error_stage'], 'extraction')
            self.assertNotIn('secret-in-error', result['error'])

    def test_fetch_failures_always_close_page(self):
        for status, url, body in [(404, agent.canonical_pep_url(8), 'text'),
                                  (200, 'https://example.com', 'text'),
                                  (200, agent.canonical_pep_url(8), ' ')]:
            page = Mock(url=url)
            page.goto.return_value.status = status
            page.locator.return_value.inner_text.return_value = body
            browser = Mock()
            browser.new_page.return_value = page
            with self.assertRaises(RuntimeError):
                agent.fetch_source(browser, agent.canonical_pep_url(8), 8)
            page.close.assert_called_once()

    def test_fetch_success_and_missing_response(self):
        page = Mock(url=agent.canonical_pep_url(8))
        page.goto.return_value.status = 200
        page.locator.return_value.inner_text.return_value = 'Status: Active'
        browser = Mock()
        browser.new_page.return_value = page
        with patch.object(agent, 'EVIDENCE_DIR', self.root / 'evidence'):
            text, url, file = agent.fetch_source(browser, agent.canonical_pep_url(8), 8)
        self.assertEqual(Path(file).read_text(), text)
        page.goto.return_value = None
        with self.assertRaises(RuntimeError):
            agent.fetch_source(browser, agent.canonical_pep_url(8), 8)

    def test_extraction_rejects_empty_and_invalid_json(self):
        client = Mock()
        for text in ['', 'not json', '{"value":42}']:
            client.models.generate_content.return_value.text = text
            with self.assertRaises(Exception):
                agent.extract_attribute('page', 8, 'status', client)
        client.models.generate_content.return_value.text = '{"value":null,"evidence_quote":null}'
        self.assertIsNone(agent.extract_attribute('page', 8, 'status', client).value)

    def test_reference_failure_and_shape(self):
        with patch.object(agent.requests, 'get') as get:
            get.return_value.json.return_value = []
            with self.assertRaises(RuntimeError):
                agent.load_reference_data()
            get.return_value.raise_for_status.side_effect = RuntimeError('HTTP failure')
            with self.assertRaises(RuntimeError):
                agent.load_reference_data()

    def test_csv_headers_filter_empty_and_utf8_bom(self):
        path = self.root / 'input.csv'
        path.write_text('wrong,headers\n1,2\n')
        with self.assertRaises(ValueError):
            agent.read_records(path)
        path.write_text('\ufeffpep_number,attribute,current_value\n8,status,\n20,type,\n', encoding='utf-8')
        self.assertEqual(len(agent.read_records(path, 8)), 1)
        with self.assertRaises(ValueError):
            agent.read_records(path, 999)
        path.write_text('pep_number,attribute,current_value\n')
        with self.assertRaises(ValueError):
            agent.read_records(path)

    def test_csv_round_trip_and_no_temp_left(self):
        result = agent.process_record(dict(self.row, pep_number='bad'), None, {}, None, None)
        with patch.object(agent, 'OUTPUT_FILE', self.root / 'results.csv'):
            agent.save_results([result])
        import csv
        with (self.root / 'results.csv').open() as f:
            self.assertEqual(list(csv.DictReader(f))[0]['decision'], 'ERROR')
        self.assertFalse((self.root / 'results.csv.tmp').exists())

    def test_missing_key_fails_before_network(self):
        with patch.object(agent, 'load_dotenv'), patch.dict(agent.os.environ, {}, clear=True), \
             patch.object(agent, 'load_reference_data') as reference:
            with self.assertRaisesRegex(RuntimeError, 'SERPAPI_KEY'):
                agent.main(['--input', 'records.csv'])
            reference.assert_not_called()

    def test_main_continues_after_bad_row_and_preserves_output(self):
        input_path = self.root / 'batch.csv'
        input_path.write_text('pep_number,attribute,current_value\nbad,status,\n8,status,Draft\n')
        output = self.root / 'run'
        browser = Mock()
        playwright = Mock()
        playwright.chromium.launch.return_value = browser
        with patch.object(agent, 'INPUT_FILE', Path('records.csv')), \
             patch.object(agent, 'OUTPUT_FILE'), patch.object(agent, 'EVIDENCE_DIR'), \
             patch.object(agent, 'load_dotenv'), \
             patch.dict(agent.os.environ, {'SERPAPI_KEY': 'test', 'GEMINI_API_KEY': 'test'}), \
             patch.object(agent.serpapi, 'Client'), patch.object(agent.genai, 'Client'), \
             patch.object(agent, 'load_reference_data', return_value=self.reference), \
             patch.object(agent, 'sync_playwright') as factory, \
             patch.object(agent, 'discover_source', return_value=dict(url=agent.canonical_pep_url(8), query='PEP 8', method='serpapi', search_issue='')), \
             patch.object(agent, 'fetch_source', return_value=('Status: Active', agent.canonical_pep_url(8), str(self.evidence))), \
             patch.object(agent, 'extract_attribute', return_value=agent.Extraction(value='Active', evidence_quote='Status: Active')):
            factory.return_value.__enter__.return_value = playwright
            args = ['--input', str(input_path), '--output-dir', str(output)]
            self.assertEqual(agent.main(args), 1)
            import csv
            with (output / 'results.csv').open() as f:
                rows = list(csv.DictReader(f))
            self.assertEqual([r['decision'] for r in rows], ['ERROR', 'ACCEPT'])
            self.assertEqual(json.loads((output / 'manifest.json').read_text())['record_count'], 2)
            before = (output / 'results.csv').read_bytes()
            with self.assertRaises(FileExistsError):
                agent.main(args)
            self.assertEqual((output / 'results.csv').read_bytes(), before)
            browser.close.assert_called_once()

    def test_different_page_captures_keep_distinct_evidence(self):
        page = Mock(url=agent.canonical_pep_url(8))
        page.goto.return_value.status = 200
        page.locator.return_value.inner_text.side_effect = ['Status: Draft', 'Status: Active']
        browser = Mock()
        browser.new_page.return_value = page
        with patch.object(agent, 'EVIDENCE_DIR', self.root / 'evidence'):
            first = agent.fetch_source(browser, agent.canonical_pep_url(8), 8)[2]
            second = agent.fetch_source(browser, agent.canonical_pep_url(8), 8)[2]
        self.assertNotEqual(first, second)
        self.assertEqual(Path(first).read_text(), 'Status: Draft')
        self.assertEqual(Path(second).read_text(), 'Status: Active')


if __name__ == '__main__':
    unittest.main()
