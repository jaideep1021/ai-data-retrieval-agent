# Deliverable 2 findings — 2026-10-28

SerpApi and Brave live smoke tests completed. The subsequent benchmark is documented
in evaluation-step3-findings.md.

## Actual verification

- Full suite: **52 tests passed**, including the baseline's local Chromium test.
  This comprises the previous 35 tests plus 17 new multi-source/provider tests.
- New tests exercise matching claims, differing claims, exact duplicate text,
  redirects to the same page, unsupported quotations, isolated source failures,
  invalid selection indices, empty search, all-provider failure, partial provider
  recovery, existing-output preservation, provider response normalization,
  Brave authentication-header wiring, refused redirects, 401/403/429/500 statuses,
  malformed JSON, and missing provider configuration.
- `pip check`: no broken requirements found. Existing dependency pins suffice.
- Initial sandbox execution blocked Chromium's macOS launch and network access.
  Re-running the browser suite and the bounded live check with permitted access
  succeeded. The initial network-blocked run remains as an ERROR record locally;
  it is not counted as a provider-service failure or benchmark observation.

## Live SerpApi smoke test

Command:

```sh
python multisource.py --entity "PEP 703" --attribute title --provider serpapi --max-sources 3
```

Local artifact: `runs/multisource-20261028T211827742699Z/result.json`.
The run took **10.387 seconds**, made **2 search calls** and **7 model calls**,
and captured **3 grounded page claims**. Outcome: **CONFLICT**, exit code 2.
The exit code is intentional for a review-needed outcome, not a crashed run.
Queries were `PEP 703 title` and `site:python.org "PEP 703" title`.

| Source | Extracted value |
|---|---|
| python/peps GitHub source, pep-0703.rst | Making the Global Interpreter Lock Optional in CPython |
| discuss.python.org topic 22606, post 123 | Making the Global Interpreter Lock Optional |
| python/steering-council GitHub issue 188 | Making the Global Interpreter Lock Optional in CPython |

The comparison surfaced a shortened discussion heading versus the full document
title. **This is not evidence of a factual contradiction.** Selection/extraction
still admitted commentary despite instructions to prefer original metadata.
The saved quotations make this problem visible for human review. Do not count
this as successful semantic verification or independent corroboration. These
pages are related to the same Python project; distinct hosts do not establish
independent publishers. The comparator deliberately does not choose the majority
answer or mark truth verified.

This is one development smoke test on the same familiar PEP used during
Deliverable 1. It is not an accuracy estimate, held-out benchmark, or evaluation
of general business attributes. The API token-usage records are saved locally;
no dollar cost is asserted without provider billing/rate verification.

## Live Brave smoke test

After the user added the key locally, the same command with `--provider brave`
completed on 2026-10-28. Key values were never displayed.

Local artifact: `runs/multisource-20261028T214836086789Z/result.json`.
Elapsed time: **10.657 seconds**. Both search requests succeeded and each returned
10 candidates. Seven model calls produced three mechanically grounded claims.
Outcome: **CONFLICT**, exit code 2.

| Source | Extracted value |
|---|---|
| peps.python.org/pep-0703/ | Making the Global Interpreter Lock Optional in CPython |
| github.com/python/cpython/issues/108219 | PEP 703 -- Making the Global Interpreter Lock Optional in CPython |
| github.com/python/steering-council/issues/188 | Making the Global Interpreter Lock Optional in CPython |

This is a formatting-related false conflict: one extraction included the document
identifier prefix. It does not demonstrate factual disagreement. Brave discovery,
retrieval, extraction, and audit persistence worked live; semantic comparison
still needs the documented human review. Related Python project pages do not
establish source independence. No truth verdict is asserted.

The SerpApi and Brave times are single development observations with different
queries/pages and uncontrolled caches/network/model latency. They cannot rank
provider speed or quality. The combined `both` mode has offline coverage but has
not been live-tested. The 20–50 observation evaluation remains Deliverable 3.

## Discussion before Deliverable 3

Agree on how to score partial/shortened titles and related-source duplication.
The current conservative output exposes string differences for review; it does
not implement semantic equivalence, source ownership verification, or automated
truth adjudication. Those limits must carry into the evaluation design rather
than being hidden in an accuracy number.
