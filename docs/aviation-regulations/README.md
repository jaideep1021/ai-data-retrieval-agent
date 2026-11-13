# Aviation extension: setup and status

Development update, 12 November 2026; existing package version and tags unchanged.
Start with [progress summary](progress-summary-20261113.md). The latest live US–South Africa trial produced zero verified events. Offline tests do not establish regulatory accuracy.

## Fresh setup
From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-business.txt
python -m unittest discover -s tests -q
```

Windows activation: `.venv\Scripts\activate`. Copy `.env.example` to `.env` and configure Gemini, SerpApi and Brave locally. Never publish the keys. The existing baseline browser path additionally needs `python -m playwright install chromium`.

## Bounded live trial (uses API allowances)

```sh
python aviation_agent.py --tasks examples/aviation-regulations/commercial-tasks.json --task-id ZAF-us_bilateral_air_services --output runs/my-new-trial
```

Use a new output directory. Shared planning and both providers together allow at most 14 model attempts; each provider has two searches, three parent attempts and two attachments. Seven-second model pacing is configured. Service quotas can still stop the batch.

Optional `--ocr-screening` requires Tesseract English data and Poppler (`tesseract`, `pdftoppm`, `pdfinfo` on PATH). On macOS use `brew install tesseract poppler`; on Ubuntu use `sudo apt install tesseract-ocr tesseract-ocr-eng poppler-utils`. Windows users must install those tools separately and add them to PATH. OCR is capped at one parent attempt per provider and three pages per attempt. It supplies review recommendations, not verified events. Missing tools are recorded as unavailable.

## Review and reproduction boundaries
Raw runs, PDFs and private human labels are not shipped. Historical paths in findings refer to local evidence, not files included in a fresh clone. Re-running live search will not reproduce identical results. `prepare_simple_review.py` packages the historical Kenya development fixtures and is not a universal review-queue generator. The UI/server are included, but need a prepared local review pack and labels path. The launcher takes these as arguments.

```sh
python aviation_review_server.py --pack runs/YOUR_PACK/review-pack.json --labels runs/YOUR_PACK/human-labels.csv --port 8765 --open-browser
```

No final commercial event CSV is claimed. See [implementation review](implementation-review-step5.md), [OCR integration](ocr-screening-integration.md), [latest trial](navigation-ocr-live-check.md) and [navigation refinement](navigation-relevance-check.md). Code and sanitized reports are publishable; local correspondence, credentials and raw evidence remain excluded.
