# Changelog

## 0.2.0 — 2026-10-29

Combines autonomous search, multi-source comparisons, measured evaluation and
business-dataset preparation while retaining the v0.1.0 baseline.

### Deliverable 1 — autonomous search (2026-10-28)

Added a separate `autonomous.py` development path with generated queries,
search-result selection, bounded static retrieval, evidence checks and an audit
record. Added offline failure-path tests and reproduction documentation. The
baseline implementation, dependency pins and `v0.1.0` tag are unchanged.
This is a single-source development milestone, not the multi-source benchmark.

### Deliverable 2 — multi-source comparison (2026-10-28)

Added `multisource.py`, SerpApi/optional Brave adapters, per-source evidence and
failure records, bounded query retries, normalized value grouping, conflict and
duplicate reporting, 17 offline tests, and setup/findings documentation. Full
suite: 52 passed including Chromium. SerpApi live test exposed a shortened-title
mismatch; semantic verification is not claimed. Brave live check also completed and exposed a title-prefix formatting mismatch.
Original baseline and Deliverable 1 implementation remain unchanged.

### Deliverable 3 — performance evaluation (2026-10-28)

Added a frozen 20-record benchmark, an instrumented evaluator preserving both
pipelines, scoring/cost tests, and an offline sanitized report generator. The
paced run completed 60 trials: candidate accuracy baseline 20/20, autonomous
SerpApi 1/20, autonomous Brave 18/20; accepted-correct outputs 20/20, 0/20 and 6/20.
All baseline trials used canonical fallback. Preserved the initial rate-limited
run separately and added pacing plus a 429 stop safeguard. Full test suite: 60
passed; 55 evidence hashes verified. Documented costs as estimates and retained
failure/abstention cases. The original run and its failure records were preserved.

### Deliverable 4 — business dataset selection (2026-10-28)

Selected DOT historical airline fares; prepared a seeded 30-market 2024 Q4 sample,
30 proposed retrieval tasks, separate reference answers, and source/hash/license
provenance. Added a bounded download/offline-replay tool and seven validation tests.
Full suite: 67 passed. Documented comparison with supply-chain data, field meanings,
research questions and limitations. No business-agent evaluation was performed.

### Deliverable 5 — consolidated report and local release review (2026-10-28)

Added the Week 2 research report, version-specific reproduction instructions and
release review. Corrected the README's Week 1/Week 2 distinction and roadmap;
prepared package version 0.2.0 while preserving evaluated implementation versions.
Excluded machine-specific editor settings without deleting them. Installed pinned
dependencies in a fresh environment and passed all 67 tests against a clean source
copy, including local Chromium. No business-agent upgrade or new paid benchmark was run.

## 0.1.0 — 2026-10-23

First versioned Week 1 baseline for Dr. Sibdari. Preserves SerpApi → canonical
fallback → Playwright → Gemini → deterministic verification and the original eight
synthetic records. Initial Git commit retains inspected prototype source files.

Added reproducible Python package pins, configuration template, secret/output
ignores, cross-platform setup, tests, CI, architecture assets, provenance manifest
and reference snapshot. Fixed malformed PEP IDs escaping row-level error handling;
added CSV header validation, page input URL check and credential-safe errors.

**Compatibility change:** outputs now live in unique `runs/` subfolders instead of
overwriting `results.csv`/`evidence/`. Existing output directories are rejected.
Added `--input`, `--output-dir`, `--env-file`, `--version`. Technical row failures
return exit status 1. Input CSV and the four decision meanings are unchanged.
See docs/verification.md for observed tests; no general accuracy claim is made.
