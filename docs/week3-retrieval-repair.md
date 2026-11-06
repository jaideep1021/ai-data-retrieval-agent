# Week 3 retrieval repair and repeated development pilot

This work addresses the first DOT pilot's document-access failures, missing query
proposal diagnostics and transient model errors. Only the six development cases
are used. The original pilot and the 24 held-out observations remain unchanged.

## Implementation

- `business_documents.py` extracts PDF text in a separate process with a 30-second
  timeout. It preserves layout and page markers, rejects encrypted/image-only
  documents, and limits page count, decoded streams and extracted text. It does
  not execute embedded scripts or perform OCR. Process isolation and size checks
  are practical research limits, not a hardened hostile-document sandbox.
- `BusinessRetriever` preserves binary downloads and hashes original response
  bytes. PDFs and original source bodies are saved privately alongside extracted
  text. Its maximum document response is now 10 MB; robots responses remain
  limited to 2 MB. Public-HTTPS, redirect and robots checks remain enforced.
- HTML table cells stay together as rows. Literal data/download links are ranked
  before navigation links, without hard-coded publisher domains or dataset IDs.
  At most 500 HTML links are scanned and 40 retained. JSON and CSV remain supported;
  XLSX and JavaScript-only tables remain unsupported.
- Long text prioritizes lines containing both requested markets, retaining a
  document introduction and nearby row context. It uses question identifiers,
  never reference answers or the current questionable value. Selected offsets
  remain logged. Layout extraction and context selection can still omit headers
  or associate a value with the wrong row; evidence needs audit.
- Query proposals are saved before validation. One repair opportunity per round
  includes the local rejection reason and retrieval failure feedback. The
  maximum remains two search requests and ten logical model calls per trial.
- Source selection now uses a schema allowing zero or one index, matching the
  runtime rule. Invalid multi-index selections are rejected rather than silently
  choosing a convenient result.
- Transient model HTTP 500/502/503/504 errors get at most one retry after ten
  seconds. Every attempt is logged and paced; authentication/quota errors are
  never retried. Limits include retries: twelve HTTP attempts per trial and
  120 for the batch. SDK-internal retries remain disabled.

PDF extraction uses the documented pypdf layout mode:
[pypdf text extraction](https://pypdf.readthedocs.io/en/6.21.4/user/extract-text.html).
The dependency is pinned in `requirements-business.txt`; the original environment
pins are retained in `requirements.txt`.

## Reproduce

Activate the installed project environment, then:

```sh
python -m pip install -r requirements-business.txt
python -m unittest discover -s tests
python evaluate_business.py check
python evaluate_business.py run --output-dir runs/week3-dot-repair-NEW
python evaluate_business.py score --output-dir runs/week3-dot-repair-NEW
```

Use a new output directory. The defaults run only airfare-01 through airfare-06
with both providers. Scoring is a separate offline command. Supply `--rates` only
with explicit pricing assumptions; absent rates mean unknown cost, not zero.
No original source URL, known dataset endpoint or reference answer enters agent
inputs. Manual parser diagnostics are excluded from autonomous success metrics.

## Run history

1. `week3-dot-pilot-20261105-v1`: original complete 12-trial pilot, documented in
   [the original findings](week3-dot-pilot.md). Its reports and source snapshot
   remain unchanged.
2. A parser diagnostic read the PDF already discovered in v1, without search or
   model calls. It extracted 338,875 characters from 51 pages of a 683,921-byte
   document. This verifies format support, not autonomous answer retrieval.
3. `week3-dot-pilot-20261105-v2`: diagnostic run stopped after three completed
   trials and an interrupted fourth. It used 17 model attempts. The live output
   exposed a mismatch between the old five-index selection schema and the
   one-index runtime policy. Completed and interrupted artifacts and source files
   are preserved; these observations are not pooled with the final comparison.
4. `week3-dot-pilot-20261105-v3`: paired rerun after the schema correction. Results
   are recorded below after execution and offline scoring.

The live comparison used `week3-part2-dev3`; the current validator is `week3-part2-dev4`. These are experimental labels,
not a GitHub release. Original version tags are unchanged. The same development
sample is reused, so any gains are exploratory rather than held-out evidence.

## Results

The v3 live run completed all 12 trials. Sanitized metrics and usage are in
[week3-retrieval-repair-results.json](week3-retrieval-repair-results.json).

| Measure | SerpApi original v1 | SerpApi repaired v3 | Brave original v1 | Brave repaired v3 |
| --- | ---: | ---: | ---: | ---: |
| Development trials | 6 | 6 | 6 | 6 |
| Contextually correct answers | 0/6 | 0/6 | 0/6 | 0/6 |
| Trials capturing a page | 2/6 | 2/6 | 3/6 | 5/6 |
| Accepted answers | 0 | 0 | 0 | 0 |
| Trial errors | 3 | 1 | 4 | 0 |
| Mean seconds including pacing and retries | 38.26 | 42.66 | 36.08 | 50.46 |

All 19 search attempts in the repaired run succeeded: 9 SerpApi and 10 Brave.
The run used 73 actual Gemini attempts, including four HTTP 503 failures. All four
recovered on their single permitted retry. There were no recorded HTTP 429 errors.
The remaining trial error was query-validation exhaustion: the model proposed an
undiscovered domain twice despite repair feedback. The rejected proposals and
reasons are now available rather than lost.

Brave's repaired run captured two PDF sources. This establishes working document
access, not accurate retrieval of the required record. No values were accepted;
accepted precision and cost per correct accepted answer remain undefined. The
small reused sample, changed queries and service variation prevent causal claims
that PDF support alone produced the increase in page capture.

### Evidence audit and numeric formatting correction

Three non-null values were extracted in the live run. One was an airport-wide
itinerary fare ($429.25) without the requested destination market; another was
$325 from the third-quarter report when the question requested Q4. Both remain
contextually unsuitable. The Q4 PDF also supplied a daily passenger count of
`3,109` for Dallas/Fort Worth to Orlando.

The live v3 validator rejected `3,109` because it accepted only ungrouped decimal
strings. The v4 correction accepts standard comma-separated groups of three,
while rejecting malformed grouping, negative values and non-finite numbers. It
performs no rounding and does not use reference answers. Tests cover the change.

`replay_business_validation.py` reapplied only deterministic validation to saved
v3 claims and evidence, without new searches or model calls. Original files and
trial errors were preserved. The grouped passenger value becomes grounded and
context-matching, but 3109 differs from the reference 3108.913043 by 0.086957,
exceeding the unchanged 0.01 tolerance. Overall exact accuracy remains 0/6 for both
providers after replay. The replay is not a new independent trial; its acquisition
time and API usage are inherited and must not be counted twice.

```sh
python replay_business_validation.py --source runs/week3-dot-pilot-20261105-v3 --output-dir runs/week3-validation-replay-NEW
python evaluate_business.py score --output-dir runs/week3-validation-replay-NEW
```

The current v4 code has been tested offline and replayed over saved evidence; it
has not been subjected to another full live search run. The exact v3 source files
are preserved in that run's private `source-snapshot/` directory.

### Costs and validation

Costs use the same explicit scenario assumptions as the first pilot: SerpApi
$0.025/search, Brave $0.005/search, Gemini $0.30/million input tokens,
$0.03/million cached input tokens and $2.50/million output/thinking tokens. These
are comparison assumptions, not account invoices. Failed model requests without
usage metadata keep the full estimated total unknown. Known-usage subtotals below
exclude that unknown usage and do not subtract free allowances or credits.

The interrupted v2 diagnostic and completed v3 rerun together used 90 Gemini
attempts. The replay used zero additional API calls. Diagnostic usage is recorded
separately from the paired comparison.

Validation: 105 tests passed and one optional browser test was skipped. The new
checks cover real synthetic PDF extraction, binary preservation, table rows,
public redirects, robots and response limits, query diagnostics, source-schema
limits, transient retries, request caps, grouped decimals and offline replay.
Dependency checks and Git whitespace checks passed. CI installation and README
setup now include the pinned PDF dependency. CI has not been run remotely because
nothing has been pushed.

### Research interpretation and next work

The repair improved access and reduced interrupted trials, but it did not solve
exact DOT retrieval. The remaining obstacles are business-specific: different
quarters, different fare definitions and rounded publication tables versus
full-precision structured records. Authoritative publication alone is insufficient
when the selected record or definition is wrong.

Before running the 24 held-out observations, the next development target is
source discovery leading to full-precision machine-readable records, with their
period and field definitions. Do not silently relax tolerances to make rounded PDF
values pass. If a rounded-value metric is useful, define and report it separately.
Authority-aware verification and the additional retrieval-service comparison
remain later deliverables. No general provider winner is established here. No
GitHub push, release tag change or held-out execution occurred.

### Recorded partial cost scenarios

| Run | Provider | Model attempts | Usage records | Searches | Known model usage USD | Search scenario USD |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Interrupted diagnostic v2 | serpapi | 8 | 7 | 2 | 0.008622 | 0.050 |
| Interrupted diagnostic v2 | brave | 9 | 9 | 2 | 0.009160 | 0.010 |
| Paired live v3 | serpapi | 32 | 31 | 9 | 0.023461 | 0.225 |
| Paired live v3 | brave | 41 | 38 | 10 | 0.041004 | 0.050 |
