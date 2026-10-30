# Deliverable 3 — paired development evaluation

This evaluates the frozen Week 1 implementation and the current multi-source
autonomous implementation on 20 distinct PEP records. It does not modify their
selection/extraction behavior or start the business-dataset deliverable.

## Design fixed before execution

- 20 unique PEPs sampled using Python `random.Random(20261028)` from the official
  PEP JSON endpoint, restricted to numbers >=100 with nonempty title, status,
  type and created fields. The eight previous demonstration PEPs are excluded.
- Five observations per attribute: title, status, type, created. Each PEP appears
  once. This is a small public-document development sample, not evidence of
  broad business-domain performance or absence of model training contamination.
- Frozen observations and reference answers: `examples/evaluation-20.json`.
  Contains reference endpoint, response SHA-256, capture time, sampling seed,
  eligible population size and exclusions. Do not regenerate to obtain a better
  score. A new preparation refuses to overwrite this file.
- Three configurations per observation (60 total trials): original `agent.py`,
  `multisource.py` with SerpApi, and `multisource.py` with Brave.
- Order rotates per observation to reduce simple ordering effects. There is no
  model-output cache or retry of failed observations in the evaluator. A separately
  labelled run uses a minimum seven-second model-call interval and stops on a
  Gemini 429 response; the initial unpaced run is preserved as a quota incident. Provider
  caches and any SDK-internal retries are outside this control.
- Autonomous source-attempt cap is three, with the existing two-query limit.
  Neither the baseline nor autonomous code is tuned during the benchmark.
- Same Gemini model setting for every configuration. Each run manifest captures
  the model, Python/platform, benchmark hash, source/dependency-file hashes,
  start/end times and source-attempt cap. All detailed runs remain local/ignored.

## Fairness and oracle boundary

The baseline has a known official domain, canonical URL fallback, and reference
answers for verification. It is specialized for PEPs. The autonomous modes receive
only `PEP <number>` and the requested attribute, not source URLs, current values,
or the expected answer. The evaluator scores saved outputs against the frozen
answers afterward. Baseline reference validation is intentionally retained.

This is a comparison of complete systems with different capabilities, not a
controlled experiment isolating search-engine quality. Baseline Playwright uses
rendered body text; autonomous retrieval uses static cleaned text and robots
checks. Browser setup and reference preparation are excluded from per-record time.
Browser is reused for baseline trials; autonomous retrievers are fresh per trial.

## Metrics and denominators

All 20 observations, including errors and abstentions, remain in each denominator.

- **Candidate accuracy**: exact match after whitespace/case folding, divided by
  all observations. The baseline's extracted value is its candidate. Autonomous
  candidate is the first mechanically grounded claim in retrieval order. The
  reference answer never selects among multiple candidates. This diagnostic does
  not imply the multi-source system accepted the candidate.
- **Retrieval success**: at least one page's evidence text was captured, divided
  by all observations. Retrieval of an irrelevant page can count; relevance and
  correct extraction are separate metrics. It is not search-API success rate.
- **Grounded coverage**: observations with a mechanically supported candidate.
  Baseline quote checks and autonomous value/entity/quote checks differ.
- **Accepted coverage**: baseline ACCEPT/NO_CHANGE or autonomous
  AGREEMENT_OBSERVED. The latter still does not assert truth or independence.
- **Accepted precision**: accepted correct candidates / accepted observations.
  Null when none were accepted. Baseline acceptance already depends on the oracle,
  so its acceptance precision is not an independent scientific validation.
- **Accepted-correct rate**: accepted correct candidates / all observations.
  This separates a correct single-source answer from a multi-source agreement.
- **Time**: wall time for each full pipeline call, including errors; mean, median,
  and total. Excludes client/browser setup and scoring. Includes model-call pacing
  waits in the paced run; these timings measure operation under the configured
  rate limit, not raw provider speed.
- **Usage/cost**: logical search attempts, model calls, returned input and output
  token counts, and a documented paid-tier cost scenario. SDK-internal retries
  may add HTTP requests. Missing usage is not assumed to mean no billed usage.

No semantic title repair, date conversion, unit normalization, or synonym scoring
is applied after observing results. Formatting differences therefore count as
candidate errors or conflicts; examples are inspected in the findings report.
No accuracy confidence/generalization claim follows from this small sample.

## Cost scenario (checked 2026-10-28)

The calculation is reproducible, **not an account invoice**:

- Gemini 3.5 Flash-Lite Standard paid tier: $0.30/million input tokens,
  $0.03/million cached input tokens, $2.50/million output tokens including thinking.
  Cached tokens are subtracted from ordinary input before charging the cached rate.
  Unknown model names yield null model/total estimates, not guessed pricing.
- SerpApi Starter allocation scenario: $25/1,000 searches = $0.025 per attempted
  search. This is an amortized plan scenario, not a marginal per-call charge.
  SerpApi says cached/failed searches are not counted; treating all attempts as
  allocated searches can overstate actual usage. Free quotas may reduce payment.
- Brave Search list-price scenario: $5/1,000 requests = $0.005 per attempt, before
  included credits. Actual account plan, credits, and invoice have not been read.
- Gemini responses without usage leave cost incomplete. Recorded tokens only are
  priced; unknown consumption on failures is not inventively filled in.

Official pricing references:
https://ai.google.dev/gemini-api/docs/pricing
https://serpapi.com/pricing
https://brave.com/search/api/

## Reproduction

Activate the project environment from the README and configure all three keys in
local `.env`. From the project root:

```sh
python -m unittest discover -s tests -v
python evaluate.py run --output-dir runs/my-evaluation --model-interval 7
python evaluate.py summarize --output-dir runs/my-evaluation
```

The benchmark file is reused by default. To prepare a separate new sample (same
seed, current eligible population), use a different filename:

```sh
python evaluate.py prepare --benchmark examples/new-evaluation.json
```

Do not replace the frozen benchmark for the reported run. `run` requires a new
output directory and makes live paid-service calls. It creates `manifest.json`,
`benchmark.json`, per-trial folders, `observations.json`, and `summary.json`.
Each trial checkpoints its row and the partial summary. If interrupted, inspect
how many observations/configurations completed before reporting any percentages.
On Gemini HTTP 429, the current trial is saved and evaluation stops without
further model requests. There is no resume option; a new complete run is a separate experiment and should
not replace failures in the first run. `summarize` recomputes metrics offline from
saved rows without API calls.

Keys and raw responses/evidence stay ignored. Only manually reviewed public
benchmark metadata and sanitized summaries/findings are candidates for the final
v0.2.0 release. No individual deliverable is pushed.

## Account limits confirmed during execution

The user supplied the Gemini dashboard limits: 15 requests/minute, 250,000
input tokens/minute, and 500 requests/day. The reported snapshot was 15 RPM,
23,000 TPM and 62 daily requests. This supports an RPM bottleneck for the
initial run. Seven-second call spacing limits this evaluator to under nine
model calls/minute; other clients using the same project can still consume quota.
The dashboard snapshot is not a billing statement and is not committed.

## Sampling limitation found before interpreting scores

All five sampled `type` values are `Standards Track`. Keep the frozen sample,
but do not interpret success on that field as discrimination across all PEP
types. A future benchmark should stratify by value as well as attribute; it
should be declared before running rather than replacing inconvenient records.

## Offline report regeneration

```sh
python evaluation_report.py runs/my-evaluation --output-dir docs
```

This emits `evaluation-step3-findings.md` and `evaluation-results.json` from saved
trial records. The report includes the completed-trial count and whether the run
manifest has a completion timestamp, so partial runs cannot silently masquerade
as full evaluations. Review these generated files before final publication.
