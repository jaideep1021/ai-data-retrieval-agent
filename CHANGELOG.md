# Changelog

## Unreleased — autonomous search step 1 (2026-10-28)

Added a separate `autonomous.py` development path with generated queries,
search-result selection, bounded static retrieval, evidence checks and an audit
record. Added offline failure-path tests and reproduction documentation. The
baseline implementation, dependency pins and `v0.1.0` tag are unchanged.
This is a single-source development milestone, not the multi-source benchmark.

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
