# Week 3 Research Report

Jaideep Manupati | For Dr. Soheil Sibdari | 6 November 2026

The approved DOT sample can be recovered reliably through a specialized structured-data workflow using Brave or Socrata. An audit explains why earlier correct PEP candidates were withheld. These findings motivate a cost-aware accept, retrieve or abstain policy; they do not yet demonstrate a general-purpose agent or a learned stopping policy.

## DOT experiment and service comparison

The 30 observations cover 2024 Q4 city-market fares, daily passenger counts and distances: 10 per field, with 15 missing and 15 questionable values. Six observations supported development; the remaining 24 were evaluated after freezing the core implementation. Each was tested through SerpApi, Brave and Socrata, giving 18 development and 72 held-out trials.

The agent received market IDs, period, field and unit, but no answer or source URL. The successful workflow used deterministic query templates and declared DOT schema knowledge. It discovered dataset identifiers, inspected metadata and queried exact records. It made no Gemini calls. Answers were opened only by the offline scorer.

| Service | Correct / retrieved / accepted | Mean time | Search cost* |
|---|---|---|---|
| SerpApi | 0 / 0 / 0 of 24 | 2.89 s | $1.20 |
| Brave | 24 / 24 / 24 of 24 | 8.98 s | $0.12 |
| Socrata | 24 / 24 / 24 of 24 | 8.59 s | $0 |

*Allocation scenarios, not verified invoices: $0.025 per SerpApi search and $0.005 per Brave search. Public API requests are counted separately. Held-out calls were 48 search + 24 public API for SerpApi, 24 + 144 for Brave, and 168 public API for Socrata. There were no incorrect acceptances; SerpApi accepted precision is undefined because it accepted nothing.

Development candidate accuracy was 0/6, 6/6 and 6/6 respectively. SerpApi searches succeeded, but the bounded path surfaced an airport-pair table rather than an eligible city-market table. A broad fallback query did not recover. Socrata searches a specialized public-data catalog, so these results compare workflows rather than rank general search engines.

## Verification findings and limitations

The Week 2 offline audit examined 40 autonomous PEP trials. Nineteen had correct candidates, six were accepted and thirteen were not. Twelve had only one usable grounded source; one had a title-prefix conflict. The agreement rule required two usable matching sources even when the available evidence came from an official PEP page or repository. Search failures and incorrectly scored candidates were kept separate.

The new DOT policy checks a registered publisher host, official provenance, publisher attribution and matching response origins, together with reporting period, market IDs and field interpretation. It can accept one matching original-publisher record; conflicting eligible values remain unresolved. On the same captured DOT evidence, the agreement comparator accepted none because matching Table 1 and Table 6 records were duplicates. The authority policy correctly accepted all 24 Brave and 24 Socrata cases.

Earlier LLM/PDF pilots remain documented as failures under the original tolerances. Challenges included wrong periods, airport versus city aggregation, rounded values and extraction errors. For example, 3,109 daily passengers differs from 3108.913043 by about 0.087, outside the declared 0.01 tolerance. Relevant information is not always the requested value.

The successful adapter assumes the DOT schema, units and publisher rules; it is not a universal authority classifier. All cases share one quarter and dataset family, with repetitive discovery queries. Reference answers originate from DOT, so accuracy means agreement with that benchmark, not independent proof of real-world truth. A trusted publisher can be wrong. Generalization requires new periods, schemas and conflicting-source cases.

## Research foundations

The research question connects sequential information collection, prediction with rejection and adaptive retrieval. Frazier et al. [1] motivate one-step expected improvement in terminal decision value. Ni et al. [2] support cost-sensitive rejection. Self-RAG [3] motivates selective retrieval, while truth-discovery research [4] examines conflicting sources and reliability. These are established foundations rather than evidence that our three-action formulation is novel.

A recent visual-evidence preprint explicitly studies answer, abstain or acquire additional evidence [5]. Its setting differs from business APIs, but it reinforces the need to position our contribution narrowly. Our candidate question is whether publisher provenance, context matching and source dependence improve the cost–accuracy tradeoff over fixed retrieval and confidence-only stopping.

Verification completed: 116 offline tests passed and one optional browser test was skipped. The follow-up PEP audit checked 35 saved evidence hashes; the structured runs checked 510. Core snapshots matched and the original sample remained unchanged. The freeze does not cover every transitive dependency. Raw evidence and credentials remain local; publication is pending review.

## Initial sequential decision model

Let the state contain beliefs over candidate values, evidence provenance and context, retrieval history, remaining budget and remaining steps. For numeric values, correctness uses a predeclared tolerance. Actions are accept the selected candidate, leave unresolved, or acquire evidence using an affordable tool or query. Observations include values, conflicting context, missing results and service failures.

For estimated correctness p, correct-answer utility U, error loss E and abstention loss A, the stopping value is S = max[pU − (1−p)E, −A]. The finite-horizon value is the larger of S and the best expected future value after acquisition minus its cost. At zero remaining budget or steps, only stopping actions remain.

If stopping now, acceptance is preferable when p ≥ (E−A)/(U+E). For U=0, E=100 and A=5, that is 95%. These are illustrative utility units, not an established business valuation. One-step EVSI is expected stopping value after retrieval minus current stopping value; retrieve when the best EVSI exceeds its cost. This myopic rule is not generally optimal over multiple steps.

Confidence alone is insufficient when sources are dependent or budgets differ. The present agent has verification rules, not calibrated posterior probabilities. Gemini self-confidence must not be treated as calibrated correctness. Three contiguous accept/retrieve/abstain regions are not guaranteed. Monetary and latency costs require explicit utility weights and separate reporting.

## Proposed next experiment

First validate the decision logic in a finite-horizon simulator with known source reliability, copying, stale periods and failure outcomes. Compare one-step lookahead with exact dynamic programming under the same model. Then collect new business cases with separate training, calibration and held-out groups. Compare first-source, fixed-budget, authority-based, confidence-threshold and value-of-information policies under matched tools and budgets.

Measure net utility, incorrect acceptance, accepted precision, coverage, acquisition cost and latency, plus confidence calibration. Use paired uncertainty estimates and cost sensitivity analysis. Saved trajectories cannot evaluate unseen alternative queries without additional assumptions or prospective collection. Discuss error-versus-abstention costs, a fresh dataset and the acquisition budget before live trials. This policy experiment is proposed, not completed.

## Selected references and supporting files

[1] Frazier, Powell and Dayanik (2008). A Knowledge-Gradient Policy for Sequential Information Collection. doi.org/10.1137/070693424.

[2] Ni et al. (2019). On the Calibration of Multiclass Classification with Rejection. arxiv.org/abs/1901.10655.

[3] Asai et al. (2023 preprint). Self-RAG. arxiv.org/abs/2310.11511.

[4] Li et al. (2016). A Survey on Truth Discovery. doi.org/10.1145/2897350.2897352; author preprint arxiv.org/abs/1505.02463.

[5] Xu et al. (2026 preprint). Look Again Before You Abstain. arxiv.org/abs/2606.16667.

Companion files in docs/: week3-structured-findings.md, week3-rejection-audit.md, week3-literature-review.md and week3-decision-experiment-plan.md.
