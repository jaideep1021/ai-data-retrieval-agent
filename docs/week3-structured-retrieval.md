# Week 3 structured retrieval and verification

This experiment adds a domain-specific structured-data adapter to the project.
The earlier LLM/PDF experiments are preserved. The new adapter generates queries
from templates, discovers datasets, checks metadata, and requests exact rows.
It makes no Gemini calls. It is not a general-purpose LLM research agent.

## Method and source discovery

The input contains a question, city-market IDs, year, quarter, requested field,
unit and missing/questionable current value. It contains no expected answer,
dataset ID, source URL or reference tolerance. The current value is not used in
queries or verification. A known schema is a declared engineering assumption.

SerpApi and Brave receive the same template-generated discovery queries and use
the same downstream adapter. Socrata Discovery is the additional retrieval service;
it searches a specialized public-data catalog. The adapter may follow literal
links on discovered pages, then recognizes a dataset identifier and inspects its
published metadata. It constructs the documented API route only after discovery.
No particular dataset identifier is hard-coded in the retrieval module.

The query uses only the supplied period and market IDs and allows reversed market
order. It requests at most two rows: zero is missing and two is ambiguous. Airport
pair datasets are rejected because airport-level fares are not city-market fares.
Data must provide the required schema, including overall fare, passengers per day,
and nonstop distance. The unit interpretation (USD, each-way market fare,
passengers/day and miles) is a declared DOT-domain contract, not a unit convention
learned from arbitrary websites. Identity is checked using DOT city-market IDs.

## What verification establishes

Both policies run over the same captured records:

- The adapted agreement comparator requires matching values and non-duplicate
  response evidence. Identical DOT rows in different tables are duplicate evidence.
- The experimental authority-aware policy can accept one context-matching record
  when its publisher passes the explicit trust checks. Conflicting eligible values
  remain unresolved even when one source is authoritative.

The trust checks require a registered DOT data host, official dataset provenance,
named Department of Transportation attribution, an official publisher attribution
link, and matching metadata/record origins. A .gov suffix or model assertion alone
is insufficient. This is a configured domain trust policy, not cryptographic proof
or a guarantee of factual truth. A publisher error can pass these checks.
Copies from the same publisher are not treated as independent witnesses.

The answer key is opened only in the separate offline scoring command. Candidate
selection uses the first context-matching record before scoring, never whichever
candidate agrees with the answer key. The reference itself comes from DOT, so
accuracy measures agreement with the frozen DOT benchmark rather than independent
confirmation of the underlying real-world fares.

## API access versus webpage crawling

Socrata explicitly supports programmatic discovery and data queries:
[SODA consumer guide](https://dev.socrata.com/consumers/getting-started.html),
[endpoint documentation](https://dev.socrata.com/docs/endpoints).
The adapter uses the available SODA 2.x `/resource/IDENTIFIER.json` endpoint.
Migration to SODA 3 may require an app token; that is not configured here.

The public catalog and documented metadata/data API requests use a separate API
access policy from webpage crawling. This matters because the data portal's
robots file disallows general crawling. API calls retain public-HTTPS, redirect,
response-size and timeout checks, wait one second between requests, and stop the
batch on HTTP 401/403/429. General webpage link discovery still obeys robots rules.
No credentials, private endpoints or access restrictions are bypassed. Public API
calls are counted separately from paid search requests; anonymous API quotas may
still apply. No new key was needed in these tests.

## Limits and reproducibility

Each trial permits two search/catalog queries, four dataset metadata reads and
three link-page reads. Each eligible dataset causes one bounded row query. No
model calls are made. Provider order rotates by observation. There is no shared
application cache between trials, though providers may cache their own results.

Each run records input/source hashes and an exact source snapshot. Requests and
source response hashes are retained under ignored `runs/`. The run manifest gives
the acquisition time window; this version records request durations rather than
an individual wall-clock timestamp for every response. Raw metadata may contain
publisher contact details and is not intended for public commits.

The six development cases and 24 held-out cases are reported separately. A freeze
file locks the core implementation and inputs before held-out execution. Changes
after examining held-out failures require a new evaluation sample or an explicit
exploratory label. The records are already public, so this is not a pretraining
novelty claim. Several engineering choices were informed by development failures.

## Commands

Use the project's Python environment with its pinned dependencies:

```sh
python -m pip install -r requirements-business.txt
python -m unittest discover -s tests
python retrieve_record.py --record-id airfare-01 --provider socrata
```

The single-record command performs live public API requests and writes a new
private run folder. Socrata does not require a key for this tested access path.
Brave and SerpApi use their existing keys in `.env`. Do not paste keys into code.

To reproduce a new development experiment:

```sh
python evaluate_structured.py run --output-dir runs/structured-development-NEW
python evaluate_structured.py score --output-dir runs/structured-development-NEW
python evaluate_structured.py freeze --output-dir runs/structured-development-NEW
python evaluate_structured.py run --split evaluation --freeze runs/structured-development-NEW/freeze.json --output-dir runs/structured-evaluation-NEW
python evaluate_structured.py score --output-dir runs/structured-evaluation-NEW
```

`run` is live; `score` and `freeze` are offline. Do not rerun successful trials into
an earlier output folder or pool different implementations. Repeating this now
exposed benchmark is replication, not a fresh unseen test.

## Results

Both runs are complete. See [findings](week3-structured-findings.md) and
[sanitized per-trial results](week3-structured-results.json). Original failed pilots
remain in their own reports.
