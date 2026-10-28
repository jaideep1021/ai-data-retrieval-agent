"""Offline contracts for autonomous discovery; no paid calls or known answer oracle."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch

import autonomous as auto


class AutonomousTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / "run"
        self.model = Mock(model="test-model", calls=[])
        self.model.ask.side_effect = [
            auto.QueryPlan(query="PEP 703 title proposal"),
            auto.Selection(candidate_index=0, reason="Direct publication"),
            auto.Claim(value="Example title", evidence_quote="PEP 703: Example title",
                       entity_quote="PEP 703: Example title"),
        ]
        self.search = Mock()
        self.search.search.return_value = {"organic_results": [
            {"link": "https://publication.example/document", "title": "PEP 703"}]}
        self.fetcher = Mock(policy_events=[])
        self.fetcher.fetch.return_value = ("PEP 703: Example title", "https://publication.example/document")

    def execute(self):
        return auto.run("PEP 703", "title", "Unknown", self.model, self.search, self.fetcher, self.output)

    def test_generated_query_and_discovered_url_used_without_oracle(self):
        result = self.execute()
        self.assertEqual(result["decision"], "SUPPORTED_CANDIDATE")
        self.search.search.assert_called_once_with(engine="google", q="PEP 703 title proposal", num=10)
        self.fetcher.fetch.assert_called_once_with("https://publication.example/document")
        self.assertFalse(result["reference_used"])
        query_data = self.model.ask.call_args_list[0].args[2]
        self.assertEqual(query_data, {"entity": "PEP 703", "attribute": "title"})
        extraction_data = self.model.ask.call_args_list[2].args[2]
        self.assertEqual(set(extraction_data), {"entity", "attribute", "page_text"})
        self.assertEqual(json.loads((self.output / "result.json").read_text())["decision"], result["decision"])
        self.assertTrue((self.output / result["evidence_file"]).exists())

    def test_domain_or_url_query_is_rejected(self):
        for query in ["site:example.com PEP 703", "PEP 703 https://example.com", "PEP 703 example.org"]:
            with self.subTest(query=query), self.assertRaises(ValueError):
                auto.validate_query(query)

    def test_reformulation_domain_must_be_observed(self):
        domains = auto.discovered_domains([{"url": "https://discuss.example.org/topic"}])
        self.assertIn("example.org", domains)
        self.assertEqual(auto.validate_query("PEP 703 site:example.org", domains), "PEP 703 site:example.org")
        with self.assertRaises(ValueError):
            auto.validate_query("PEP 703 site:unseen.org", domains)

    def test_query_must_include_entity(self):
        self.model.ask.side_effect = [auto.QueryPlan(query="Python title")]
        result = self.execute()
        self.assertEqual(result["stage"], "query_generation")
        self.assertEqual(result["decision"], "ERROR")
        self.search.search.assert_not_called()

    def test_prohibited_query_is_logged_but_not_executed(self):
        self.model.ask.side_effect = [auto.QueryPlan(query="PEP 703 site:example.com")]
        result = self.execute()
        self.assertEqual(result["decision"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(result["query_proposals"], ["PEP 703 site:example.com"])
        self.search.search.assert_not_called()

    def test_empty_search_abstains_without_fetching(self):
        self.search.search.return_value = {}
        self.model.ask.side_effect = [auto.QueryPlan(query="PEP 703 title"), auto.QueryPlan(query="PEP 703 original publication title")]
        self.assertEqual(self.execute()["decision"], "INSUFFICIENT_EVIDENCE")
        self.fetcher.fetch.assert_not_called()

    def test_no_relevant_selection_abstains(self):
        self.model.ask.side_effect = [auto.QueryPlan(query="PEP 703 title"),
                                    auto.Selection(candidate_index=None, reason="No relevant result"),
                                    auto.QueryPlan(query="PEP 703 original publication title"),
                                    auto.Selection(candidate_index=None, reason="Still no primary result")]
        self.assertEqual(self.execute()["decision"], "INSUFFICIENT_EVIDENCE")
        self.fetcher.fetch.assert_not_called()

    def test_reformulation_uses_feedback_and_stops_after_success(self):
        self.search.search.side_effect = [{}, {"organic_results": [{"link": "https://publication.example/document"}]}]
        self.model.ask.side_effect = [auto.QueryPlan(query="PEP 703 title"),
                                    auto.QueryPlan(query="PEP 703 original publication title"),
                                    auto.Selection(candidate_index=0, reason="Primary publication"),
                                    auto.Claim(value="Example title", evidence_quote="PEP 703: Example title", entity_quote="PEP 703")]
        result = self.execute()
        self.assertEqual(result["decision"], "SUPPORTED_CANDIDATE")
        self.assertEqual(result["search_calls"], 2)
        self.assertEqual(len(result["search_attempts"]), 2)
        self.assertEqual(self.model.ask.call_args_list[1].args[2]["previous_search"]["reason"], "No organic results")
        self.fetcher.fetch.assert_called_once()

    def test_repeated_query_abstains_without_extra_search(self):
        self.search.search.return_value = {}
        self.model.ask.side_effect = [auto.QueryPlan(query="PEP 703 title"), auto.QueryPlan(query="PEP 703 title")]
        self.assertEqual(self.execute()["decision"], "INSUFFICIENT_EVIDENCE")
        self.search.search.assert_called_once()

    def test_model_cannot_invent_candidate_index(self):
        self.model.ask.side_effect = [auto.QueryPlan(query="PEP 703 title"),
                                    auto.Selection(candidate_index=5, reason="Invented")]
        self.assertEqual(self.execute()["decision"], "ERROR")
        self.fetcher.fetch.assert_not_called()

    def test_retrieval_failure_is_saved_without_raw_exception(self):
        self.fetcher.fetch.side_effect = RuntimeError("api_key=secret")
        result = self.execute()
        self.assertEqual(result["stage"], "retrieval")
        self.assertEqual(result["decision"], "ERROR")
        self.assertNotIn("secret", (self.output / "result.json").read_text())

    def test_empty_invalid_or_wrong_entity_evidence_abstains(self):
        for claim in [auto.Claim(value=None, evidence_quote=None, entity_quote=None),
                      auto.Claim(value="Wrong", evidence_quote="Example title", entity_quote="PEP 703"),
                      auto.Claim(value="Example title", evidence_quote="Example title", entity_quote="PEP 7030")]:
            self.assertFalse(auto.supported_claim(claim, "PEP 7030 Example title", "PEP 703"))

    def test_colon_in_metadata_identifier_is_supported(self):
        claim = auto.Claim(value="Example title", evidence_quote="Title: Example title", entity_quote="PEP: 703")
        self.assertTrue(auto.supported_claim(claim, "PEP: 703\nTitle: Example title", "PEP 703"))
        wrong = auto.Claim(value="Example title", evidence_quote="Title: Example title", entity_quote="PEP: 7030")
        self.assertFalse(auto.supported_claim(wrong, "PEP: 7030\nTitle: Example title", "PEP 703"))

    def test_existing_run_is_preserved(self):
        self.output.mkdir()
        (self.output / "result.json").write_text("preserve")
        with self.assertRaises(FileExistsError):
            self.execute()
        self.assertEqual((self.output / "result.json").read_text(), "preserve")

    def test_search_exception_is_saved(self):
        self.search.search.side_effect = TimeoutError("private details")
        result = self.execute()
        self.assertEqual(result["stage"], "search")
        self.assertEqual(result["error_type"], "TimeoutError")

    def test_model_invalid_json_and_usage_logging(self):
        client = Mock()
        client.models.generate_content.return_value = Mock(text="invalid", usage_metadata=None)
        model = auto.StructuredModel(client, "test")
        with self.assertRaises(ValueError):
            model.ask("query", "instruction", {}, auto.QueryPlan)
        self.assertEqual(model.calls[0]["status"], "error")
        self.assertIsNone(model.calls[0]["usage"])
        self.assertIn("seconds", model.calls[0])
        sent = client.models.generate_content.call_args.kwargs["config"]["response_schema"]
        self.assertNotIn("additionalProperties", sent)
        client.models.generate_content.return_value.text = '{"query":"PEP 703 title","unexpected":true}'
        with self.assertRaises(ValueError):
            model.ask("query", "instruction", {}, auto.QueryPlan)

    def test_public_url_blocks_local_private_and_credentials(self):
        for url in ["http://example.com", "https://user:password@example.com", "https://example.com:8443"]:
            with self.assertRaises(ValueError):
                auto.public_url(url)
        with patch.object(auto.socket, "getaddrinfo", return_value=[(2, 1, 6, "", ("127.0.0.1", 443))]):
            with self.assertRaises(ValueError):
                auto.public_url("https://localhost/")

    def test_redirect_destination_checked_before_request(self):
        session = MagicMock()
        response = Mock(status_code=302, headers={"Location": "https://127.0.0.1/"})
        session.get.return_value.__enter__.return_value = response
        retriever = auto.Retriever(session)
        with patch.object(auto, "public_url", side_effect=["https://example.com", ValueError("private")]):
            with self.assertRaises(ValueError):
                retriever.read("https://example.com", check_robots=False)
        session.get.assert_called_once()

    def test_robots_missing_allowed_disallow_and_outage_blocked(self):
        retriever = auto.Retriever(Mock())
        with patch.object(retriever, "read", return_value=(404, "text/html", "", "https://example.com/robots.txt")):
            retriever.check_policy("https://example.com/page")
        retriever.robots.clear()
        with patch.object(retriever, "read", return_value=(200, "text/plain", "User-agent: *\nDisallow: /", "https://example.com/robots.txt")):
            with self.assertRaises(ValueError):
                retriever.check_policy("https://example.com/page")
        retriever.robots.clear()
        with patch.object(retriever, "read", return_value=(503, "text/plain", "", "https://example.com/robots.txt")):
            with self.assertRaises(ValueError):
                retriever.check_policy("https://example.com/page")

    def test_html_cleaning_and_unsupported_content(self):
        retriever = auto.Retriever(Mock())
        with patch.object(retriever, "read", return_value=(200, "text/html", "<main>PEP 703<script>bad()</script> Example title</main>", "https://example.com")):
            text, _ = retriever.fetch("https://example.com")
            self.assertIn("Example title", text)
            self.assertNotIn("bad()", text)
        with patch.object(retriever, "read", return_value=(200, "application/pdf", "PDF", "https://example.com")):
            with self.assertRaises(ValueError):
                retriever.fetch("https://example.com")


if __name__ == "__main__":
    unittest.main()
