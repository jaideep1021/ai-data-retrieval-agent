"""Three lightweight web-scraping explanations for an academic demo.

1) Parse a public PEP page using requests + BeautifulSoup.
2) Read the same page through Playwright Chromium.
3) Demonstrate why JavaScript-rendered DOM needs a real browser,
   using an in-memory page (no target-site scraping required).

Install: pip install requests beautifulsoup4 playwright
         python -m playwright install chromium
Run:     python scraping_demo.py
"""

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

URL = "https://peps.python.org/pep-0008/"


def static_html_demo() -> None:
    print("\n=== 1. Static HTML: requests + BeautifulSoup ===")
    response = requests.get(URL, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else "(missing)"
    print("HTTP status:", response.status_code)
    print("Document title:", title)
    print("Initial HTML length:", len(response.text), "characters")
    print("No browser JavaScript was executed.")


def playwright_demo() -> None:
    print("\n=== 2. Browser DOM: Playwright ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            response = page.goto(URL, wait_until="domcontentloaded", timeout=25000)
            if response is None or response.status >= 400:
                raise RuntimeError("Failed to load official PEP page")
            text = page.locator("body").inner_text(timeout=10000)
            print("Page title:", page.title())
            print("Visible text length:", len(text), "characters")
            matching_lines = [
                line.strip() for line in text.splitlines()
                if line.strip().startswith(("Status:", "Type:", "Created:"))
            ]
            print("Metadata-like lines:", matching_lines[:6])
            page.close()
        finally:
            browser.close()


def dynamic_dom_demo() -> None:
    print("\n=== 3. JavaScript-rendered content: controlled local HTML ===")
    html = """<!DOCTYPE html><html><body>
      <div id='status'>Loading...</div>
      <script>
        setTimeout(() => {
          document.getElementById('status').textContent = 'Published';
        }, 300);
      </script>
    </body></html>"""

    soup = BeautifulSoup(html, "html.parser")
    print("HTML parser sees:", soup.select_one("#status").get_text(strip=True))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.set_content(html, wait_until="domcontentloaded")
            page.wait_for_function(
                "document.querySelector('#status').textContent === 'Published'",
                timeout=5000,
            )
            print("After JS, Playwright sees:", page.locator("#status").inner_text())
            page.close()
        finally:
            browser.close()


if __name__ == "__main__":
    static_html_demo()
    playwright_demo()
    dynamic_dom_demo()
    print("\nDemo complete. For a real website, always check terms and crawl permissions.")
