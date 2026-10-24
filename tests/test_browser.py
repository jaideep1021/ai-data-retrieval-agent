"""Opt-in real Chromium smoke test, using local HTML only."""
import os
import unittest
from scraping_demo import dynamic_dom_demo


@unittest.skipUnless(os.getenv('RUN_BROWSER_TESTS') == '1', 'set RUN_BROWSER_TESTS=1 for local Chromium')
class BrowserTests(unittest.TestCase):
    def test_javascript_changes_dom(self):
        dynamic_dom_demo()
