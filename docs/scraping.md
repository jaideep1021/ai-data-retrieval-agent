# Scraping concepts

## Concepts and engineering decisions

### Discovery is not scraping

- **Discovery** locates *which URL* might contain an answer. SerpApi supplies search result metadata, including organic links.
- **Retrieval** requests an actual source page and checks it loaded successfully.
- **Parsing/scraping** transforms page HTML/DOM into useful structured or textual data.
- **Extraction** isolates a requested fact from that data; here Gemini returns `value` + `evidence_quote`.
- **Verification** tests a proposed fact against evidence/reference rules.

### HTML and the DOM

A page's HTML is source markup such as `<dt>Status</dt><dd>Active</dd>`. The **Document Object Model (DOM)** is a tree representation of the page that can be queried by tags, CSS selectors, or other locators. Browser JavaScript can add or modify DOM nodes after the initial HTML response. The text visible on a page may therefore differ from raw server HTML.

### Static extraction: requests + BeautifulSoup

For server-rendered content, a lightweight HTTP request and parser are often sufficient:

```python
import requests
from bs4 import BeautifulSoup

url = "https://peps.python.org/pep-0008/"
response = requests.get(url, timeout=20)
response.raise_for_status()
soup = BeautifulSoup(response.text, "html.parser")
print(soup.title.get_text(" ", strip=True) if soup.title else "No title")
```

**Pros:** fast, small memory footprint, no browser process. **Cons:** it does not run JavaScript. Parsing the entire page body may mix navigation text, article text, related links and metadata.

### DOM selectors

In a browser, selectors target the exact data-bearing element, for example `page.locator("main")` or `page.locator(".metadata")` **when those selectors exist on the target site**. Inspect the actual markup in DevTools before choosing selectors. Avoid assuming every website uses the same structure. For PEPs, a sensible future enhancement is to locate the specific metadata definition list instead of asking Gemini to read up to 12,000 characters from the page body.

### Dynamic rendering: Playwright

Playwright controls Chromium, Firefox or WebKit. A browser can execute scripts, follow client-side navigation and wait for asynchronous DOM updates. The current pipeline uses Chromium to retrieve `body.inner_text()`, but has **not** established that the PEP pages require JavaScript. For dynamic sites, wait for the desired selector/content rather than sleeping a fixed number of seconds.

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://peps.python.org/pep-0008/", wait_until="domcontentloaded")
    print(page.locator("body").inner_text()[:500])
    browser.close()
```

**Pros:** sees rendered DOM; supports sophisticated browser interactions. **Cons:** slower and more resource-intensive than direct HTTP; dynamic page behavior introduces timing and reliability problems.

### Prefer a documented API when it satisfies the need

An official JSON/API endpoint is usually more stable and cheaper to consume than HTML scraping. This prototype intentionally reads a webpage to demonstrate web retrieval, but uses the PEP JSON API as its reference. In a production data pipeline, prefer authoritative structured endpoints whenever allowed and appropriate.

### Responsible crawling and reliability

1. Review the site's terms, applicable permissions, published APIs and `robots.txt` guidance before automated collection. Robots instructions manage crawling traffic; they are not an authorization mechanism by themselves.
2. Set realistic timeouts; handle 404, 403, 429, 5xx, redirects, and malformed content explicitly.
3. Limit concurrency and per-domain request rate; use a bounded exponential backoff when the site permits retries, including `Retry-After` where applicable. Do **not** retry 403/429 aggressively or bypass CAPTCHAs/access controls.
4. Cache retrieved pages where appropriate, store fetch timestamps, and avoid recrawling unchanged URLs.
5. Use a host allowlist and validate redirected destinations before using fetched data in an agent; do not let arbitrary content supply new instructions or uncontrolled URLs.
6. Strip navigation and irrelevant text, minimize data passed to the LLM, and avoid collecting private or sensitive information unnecessarily.
7. Keep a reproducible trail: source URL, fetch timestamp, method, captured content, quote, model identifier, validation result and exception details.

For an interactive explanation, run `python scraping_demo.py`, which contrasts raw HTML parsing, live Playwright page retrieval and browser-executed JavaScript on a safe in-memory example.


## Robots and terms in this baseline

The programs do not automatically fetch or enforce robots.txt. Before a live run,
review the target site's terms, API documentation and current robots rules. Keep
runs small and serial. Do not bypass authentication, paywalls, CAPTCHAs or blocks.
Stop on access denial or rate limiting; automatic backoff and robots enforcement
are roadmap items, not implemented safeguards.

A 404 for `/robots.txt` means the file was unavailable, not that the PEP page was
missing. RFC 9309 permits crawling when robots is unavailable in the 4xx category,
but this does not grant a license or override site terms. This project uses a
conservative manual review step; treat 403/429 as a reason to stop and investigate.
For network failures or 5xx, defer collection until policy can be checked.
See [RFC 9309](https://www.rfc-editor.org/rfc/rfc9309.html).

On the baseline verification date (2026-10-23, America/New_York), the robots request
returned HTTP 404. That is an observation, not a permanent permission statement.
The [PEP API](https://peps.python.org/api/) explicitly documents its public read-only
JSON endpoint. No blanket legal permission or independent terms audit is claimed.

Only public PEP text is intended as input. The first 12,000 characters of captured
page text go to Google Gemini; the PEP search query goes to SerpApi. Check provider
terms and your organization's policies before using other data. Keep local evidence
out of public commits; respect content licenses when sharing excerpts.
