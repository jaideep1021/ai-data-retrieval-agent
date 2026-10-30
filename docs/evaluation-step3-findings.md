# Deliverable 3 — measured findings

Run: `evaluation-deliverable3-paced-20261028`. Completed trials: **60/60**.
Completion recorded: **yes**.

## Results

| Configuration | Correct / N | Candidate accuracy | Retrieval | Accepted correct / N | Accepted precision | Mean seconds | Median seconds | Cost scenario USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 20/20 | 100.0% | 100.0% | 20/20 | 100.0% | 6.75 | 6.97 | $0.5153 |
| autonomous_serpapi | 1/20 | 5.0% | 5.0% | 0/20 | undefined | 25.60 | 27.78 | $0.8207 |
| autonomous_brave | 18/20 | 90.0% | 100.0% | 6/20 | 100.0% | 34.97 | 35.00 | $0.2193 |

Candidate accuracy uses the first grounded autonomous claim, even if the system
abstained or found a conflict. Accepted-correct rate measures the more restrictive
output decision. Neither measure proves publisher independence. Times include
configured model-call pacing. Cost scenarios are not verified bills; see protocol.

## Decisions and usage

| Configuration | Decisions | Search attempts | Model calls | Input tokens | Output + thinking tokens | Usage complete |
|---|---|---:|---:|---:|---:|---|
| baseline | ACCEPT: 20 | 20 | 20 | 45594 | 643 | True |
| autonomous_serpapi | ERROR: 8, INSUFFICIENT_EVIDENCE: 12 | 32 | 73 | 51461 | 2111 | True |
| autonomous_brave | AGREEMENT_OBSERVED: 6, CONFLICT: 2, INSUFFICIENT_EVIDENCE: 12 | 33 | 100 | 147613 | 4002 | True |

## Attribute breakdown

| Configuration | Attribute | Correct / N |
|---|---|---:|
| baseline | title | 5/5 |
| baseline | status | 5/5 |
| baseline | type | 5/5 |
| baseline | created | 5/5 |
| autonomous_serpapi | title | 0/5 |
| autonomous_serpapi | status | 0/5 |
| autonomous_serpapi | type | 1/5 |
| autonomous_serpapi | created | 0/5 |
| autonomous_brave | title | 3/5 |
| autonomous_brave | status | 5/5 |
| autonomous_brave | type | 5/5 |
| autonomous_brave | created | 5/5 |

## Failure and abstention inventory

Labels may overlap within one trial. They describe observed symptoms, not an
automated determination that the source or model is factually wrong.

| Observation | PEP / field | Configuration | Decision | Diagnostic |
|---|---|---|---|---|
| obs-01 | 841 / title | autonomous_serpapi | ERROR | no captured page; run error: query_generation |
| obs-01 | 841 / title | autonomous_brave | INSUFFICIENT_EVIDENCE | candidate differs from reference |
| obs-02 | 776 / status | autonomous_serpapi | ERROR | no captured page; run error: query_generation |
| obs-02 | 776 / status | autonomous_brave | INSUFFICIENT_EVIDENCE | correct candidate, not accepted |
| obs-03 | 3156 / type | autonomous_serpapi | INSUFFICIENT_EVIDENCE | correct candidate, not accepted |
| obs-04 | 804 / created | autonomous_serpapi | ERROR | no captured page; run error: query_generation |
| obs-04 | 804 / created | autonomous_brave | INSUFFICIENT_EVIDENCE | correct candidate, not accepted |
| obs-05 | 241 / title | autonomous_serpapi | ERROR | no captured page; run error: query_generation |
| obs-06 | 799 / status | autonomous_brave | INSUFFICIENT_EVIDENCE | correct candidate, not accepted |
| obs-06 | 799 / status | autonomous_serpapi | INSUFFICIENT_EVIDENCE | no captured page |
| obs-07 | 3151 / type | autonomous_serpapi | INSUFFICIENT_EVIDENCE | no captured page |
| obs-07 | 3151 / type | autonomous_brave | AGREEMENT_OBSERVED | source retrieval: ValueError |
| obs-08 | 415 / created | autonomous_serpapi | INSUFFICIENT_EVIDENCE | no captured page |
| obs-09 | 233 / title | autonomous_brave | INSUFFICIENT_EVIDENCE | correct candidate, not accepted |
| obs-09 | 233 / title | autonomous_serpapi | ERROR | no captured page; run error: query_generation |
| obs-10 | 714 / status | autonomous_serpapi | INSUFFICIENT_EVIDENCE | no captured page |
| obs-10 | 714 / status | autonomous_brave | INSUFFICIENT_EVIDENCE | correct candidate, not accepted |
| obs-11 | 758 / type | autonomous_serpapi | ERROR | no captured page; run error: query_generation |
| obs-11 | 758 / type | autonomous_brave | INSUFFICIENT_EVIDENCE | correct candidate, not accepted |
| obs-12 | 342 / created | autonomous_brave | INSUFFICIENT_EVIDENCE | correct candidate, not accepted; source retrieval: ValueError |
| obs-12 | 342 / created | autonomous_serpapi | INSUFFICIENT_EVIDENCE | no captured page |
| obs-13 | 467 / title | autonomous_serpapi | INSUFFICIENT_EVIDENCE | no captured page |
| obs-13 | 467 / title | autonomous_brave | CONFLICT | correct candidate, not accepted; grounded strings differ; semantic review required |
| obs-14 | 202 / status | autonomous_serpapi | INSUFFICIENT_EVIDENCE | no captured page |
| obs-15 | 671 / type | autonomous_brave | INSUFFICIENT_EVIDENCE | correct candidate, not accepted; source retrieval: ValueError |
| obs-15 | 671 / type | autonomous_serpapi | INSUFFICIENT_EVIDENCE | no captured page |
| obs-16 | 436 / created | autonomous_serpapi | INSUFFICIENT_EVIDENCE | no captured page |
| obs-16 | 436 / created | autonomous_brave | INSUFFICIENT_EVIDENCE | correct candidate, not accepted |
| obs-17 | 818 / title | autonomous_serpapi | INSUFFICIENT_EVIDENCE | no captured page |
| obs-17 | 818 / title | autonomous_brave | CONFLICT | candidate differs from reference; grounded strings differ; semantic review required |
| obs-18 | 419 / status | autonomous_brave | INSUFFICIENT_EVIDENCE | correct candidate, not accepted |
| obs-18 | 419 / status | autonomous_serpapi | ERROR | no captured page; run error: query_generation |
| obs-19 | 805 / type | autonomous_serpapi | ERROR | no captured page; run error: query_generation |
| obs-19 | 805 / type | autonomous_brave | INSUFFICIENT_EVIDENCE | correct candidate, not accepted |
| obs-20 | 3123 / created | autonomous_serpapi | INSUFFICIENT_EVIDENCE | no captured page |

## Boundaries

- One frozen development sample of 20 PEPs, five records per field; no business-domain claim.
- Prior demonstration PEPs excluded; model pretraining contamination remains possible.
- Baseline uses a reference oracle for acceptance and known-domain fallback. Autonomous modes do not.
- Rotated order does not eliminate changing web results, service caches, or stochastic model behavior.
- Raw page evidence, provider results, and keys remain local and excluded from this report.
- Separate initial quota-limited run is preserved and must not be pooled with this run.
- See evaluation-step3.md for exact scoring, sampling, reproduction, and pricing assumptions.
