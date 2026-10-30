# Week 2 research report for Dr. Sibdari

**Author:** Jaideep Manupati
**Prepared:** 29 October 2026
**Package:** v0.2.0

## Research objective

Extend the successful Week 1 PEP retrieval prototype toward autonomous source
discovery and multi-source comparison, measure performance and failures, and
select a business dataset for the next experiment. The work asks how much human
source guidance can be removed while retaining traceable evidence.

## What was delivered

| Requested item | Implemented evidence | Boundary |
|---|---|---|
| Autonomous search | Generated queries, candidate selection and bounded query reformulation in autonomous.py and multisource.py | No supplied answer or source URL in automatic prompts; model prior knowledge remains possible |
| Multi-source verification | Separate page extraction, literal quotation checks, grouped values, conflicts, duplicate handling and saved provenance | Mechanical grounding and observed agreement do not establish truth or publisher independence |
| Alternative search source | Optional Brave API alongside the existing SerpApi configuration; both tested live | Provider results differ; no universal provider ranking established |
| Performance evaluation | Frozen 20-observation sample, three configurations, 60 completed live trials; timing, usage, cost scenarios and failure inventory | Small PEP-only development benchmark, not business-domain generalization |
| Business application | 30 city-market pairs from DOT historical airfare data; questions, answer key and reproducible preparation | Dataset selection/preparation complete; airline agent adaptation and evaluation not implemented |

The original agent.py remains the specialized v0.1.0 baseline. Autonomous code is
separate so both versions can be reviewed and rerun. All raw evidence and API keys
remain local; only reviewed public examples and sanitized results are included
in the repository.

## Experiment and results

Twenty distinct PEPs were sampled with a fixed seed, excluding the eight prior
demonstration PEPs. Each attribute—title, status, type, creation date—has five
observations. Every observation ran through the baseline, autonomous SerpApi and
autonomous Brave configurations, with rotated ordering. Reference answers were
frozen before execution and withheld from autonomous calls.

| Configuration | Correct candidate / 20 | Page retrieval | Correct accepted outputs / 20 | Mean elapsed time | Paid-tier cost scenario |
|---|---:|---:|---:|---:|---:|
| Baseline | 20 (100%) | 100% | 20 (100%) | 6.75 s | $0.5153 |
| Autonomous + SerpApi | 1 (5%) | 5% | 0 (0%) | 25.60 s | $0.8207 |
| Autonomous + Brave | 18 (90%) | 100% | 6 (30%) | 34.97 s | $0.2193 |

Candidate accuracy scores the first grounded autonomous claim, including trials
that abstained or flagged conflict. Accepted output requires the configuration's
acceptance rule: the baseline uses its reference oracle, while autonomous code
requires observed agreement across distinct captured texts. Agreement does not
establish independent corroboration.

**Important asymmetry:** all 20 baseline trials used the canonical URL fallback.
Its perfect score establishes performance in the assisted setting, not autonomous
search success. All five sampled type values are Standards Track, limiting the
informativeness of that field's results.

The completed paced experiment made 85 logical search attempts and 193 model
calls. Total paid-tier scenario: **$1.5553**, before credits and without invoice
confirmation. Times include a minimum seven seconds between model calls; they do
not measure raw provider latency. Returned usage was available for every model
call in this experiment. Official rate references and calculation assumptions are
in the evaluation protocol.

An initial unpaced attempt encountered Gemini HTTP 429 responses and was stopped.
Its 48 saved trials and failures were preserved separately, not replaced with
successful retries. The user confirmed a 15-RPM account limit. The evaluator was
updated with pacing and a stop-on-429 safeguard; the separate completed run had
no recorded model HTTP errors. The initial saved-trial cost scenario is $0.5938,
with incomplete failed/in-flight usage; neither figure is a verified bill.

## What failed and what it means

- Broad queries sometimes found unrelated pages. The automatic SerpApi workflow
  returned insufficient evidence on 12 observations and query-validation errors
  on eight; all its search requests returned successfully.
- Those eight reformulations introduced domains not discovered in prior results.
  The guard enforced its rule, but the agent could not recover effectively.
- Brave returned agreement on six records, insufficient evidence on 12, and
  conflicting strings on two. Correct candidates often lacked corroboration.
- Two first-candidate title mismatches included a PEP-number prefix. Conflicts
  included formatting and discussion-heading differences, not established
  contradictions between independent factual measurements.
- Official documentation, repositories and discussions may share one provenance.
  Matching pages cannot automatically be counted as independent sources.

These findings suggest the next gains should come from query specificity,
controlled recovery and better interpretation of source/field context. Switching
providers alone does not solve verification. The observed provider difference is limited to this PEP sample and does not
establish which provider is best for business data.

## Selected business dataset

Selected **DOT Consumer Airfare Report, Table 1, 2024 Q4**, after comparing airline
and logistics alternatives. Prepared 30 distinct city-market pairs from the
1,000-record quarter, using a fixed seed and preserving original decimal precision.
The sample includes fares, daily traffic, distance and carrier shares. Thirty
proposed retrieval tasks have reference answers stored separately.

This is historical aggregate airfare data, not current purchasable ticket prices.
City markets can contain multiple airports. Comparisons must align market IDs,
quarter, field, units and fare definition. The period predates the July 2025 survey
collection change; no cross-regime trend inference is attempted.

The World Bank Logistics Performance Index was considered but not implemented:
its national logistics indicators were less direct for a small price-retrieval
exercise. The DOT sample's source metadata states USGOV_WORKS; attribution and
provenance are retained. No private transaction data is used.

## Reading and reproduction

- [Quick reproduction and version guide](week2-reproduction.md)
- [Full evaluation tables](evaluation-step3-findings.md) and [interpretation](evaluation-step3-review.md)
- [Evaluation design and cost assumptions](evaluation-step3.md)
- [Business dataset, definitions and reuse metadata](business-dataset-step4.md)
- [Release validation checks](release-review-v0.2.0.md)

No business prediction model, business-domain retrieval evaluation, independent
truth-verification guarantee or remote CI success is claimed.
