# v0.1.0 verification record

Date: **2026-10-23 (America/New_York)**. Host: macOS ARM64, Python 3.13.5.

## Inspection and preservation

Inspected the existing local `ai-data-retrieval-agent` source, README, architecture,
input records and environment inventories before editing. The original folder had
no Git repository. Created a separate baseline checkout, copying only reviewed
source/docs/synthetic records; the original `.env`, both virtual environments,
results, evidence and screenshot remain untouched. Original source is retained in
the first commit. Keys were used by reference through `--env-file`, not copied.

## Executed checks

- Installed the complete `requirements.txt` in a newly created virtual environment:
  succeeded. `python -m pip check`: no broken requirements.
- `python -m playwright install chromium`: succeeded (matching installed browser
  was available; no claim that a fresh browser download was needed).
- Final `RUN_BROWSER_TESTS=1 python -m unittest discover -s tests -v`:
  **15 tests passed, none skipped**. Includes real Chromium with in-memory JavaScript.
- CLI help and offline invocation checked. The test suite also checks missing keys,
  malformed CSV, invalid model JSON, source errors, continued processing after a bad
  row, preservation of an existing run, and content-addressed evidence captures.
- Live reference endpoint: loaded **746** PEP objects. Robots endpoint: HTTP **404**.
- First live eight-record run: **7 ACCEPT, 1 ERROR, 0 REVIEW, 0 NO_CHANGE**;
  exit status **1**. PEP 572 failed at extraction with a Gemini `ServerError`.
  Processing continued and all eight rows were saved.
- Targeted PEP 572 retry: **1 ACCEPT**, value `Standards Track`, both verification
  flags true; exit status **0**. The initial failed run remains preserved locally.
  This does not turn the first run into an eight-of-eight pass.
- Final evidence-filename change was exercised in the targeted retry and in an
  offline regression test; the eight-record run preceded that filename change.

Live model: `gemini-3.5-flash-lite`. Exact observations above are specific to this
small benchmark and execution date. They are not an out-of-domain accuracy result.
The original historical eight-of-eight demonstration was not substituted for the
current verification results.

## Reproduction boundaries

Offline tests mock SerpApi/Gemini/HTTP/browser failures; they are not live integration
coverage of those providers. The optional browser test is real but uses local HTML.
Live output and evidence are deliberately excluded from Git. Each local run carries
its own model, version, input/reference hashes and page evidence hashes.

Windows and Linux were not run locally. The repository includes a three-platform
GitHub Actions workflow; inspect its actual run status before claiming it passed.
Dependency versions are pinned, but external content, model availability and API
behavior are not frozen. A new run may differ or fail because of quota or outages.

## Publication review

- Reviewed the diff against the preserved prototype and ran `git diff --check`.
- Scanned publishable files and original Git history against the actual local API
  key bytes without displaying them: no matches. Verified `.env.example` remains
  publishable and real `.env`, credentials, environments, evidence/results/runs
  are ignored. Compared original input records byte-for-byte: unchanged.
- Rendered and visually inspected the architecture PNG; SVG also included.
- Live outputs remain ignored; only the verification summary is published.
