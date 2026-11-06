# Week 3 Part 1 DOT experiment specification

Prepared 5 November 2026. The professor approved the 30 observations, as confirmed
by Jaideep in chat. Task conditions, splits, scoring and budgets below are proposed
research choices, not additional decisions attributed to the professor. At preparation, no live
Week 3 trials had been run. This document preserves the initial plan; the completed
[structured method](week3-structured-retrieval.md) and [findings](week3-structured-findings.md)
describe the final implementation and its differences from the initial pilot.

## Dataset and scope

Preserve the existing 30 city-market pairs from DOT Table 1, 2024 Q4. Each pair
contributes one existing task: 10 fare, 10 daily passenger traffic and 10 distance.
These are historical aggregate statistics, not live ticket offers. The original
Week 2 sample and answer key remain unchanged; their hashes are recorded in the
new evaluator manifest.

## Case construction

`examples/week3/agent-inputs.json` contains 30 questions, each with either a missing
value (null) or a questionable current value. Within each field, alternate missing
and questionable cases in the existing stable record order: 15 of each overall.
Questionable values are copied from another same-field observation and checked to
be outside the target reference tolerance. This is a controlled corruption test,
not a claim that DOT contains errors. Current values are untrusted inputs and must
not count as evidence. Do not tell the agent the decoy-generation procedure or donor.
A separate comparison on all-missing cases could later measure anchoring, but is
not included in this initial 30-case design.

## Development and evaluation separation

Use the first two cases per field for development: six cases, one missing and one
questionable for each field. The remaining 24 are held out from live tuning and
must be run only after freezing the implementation and policy. Report development
and evaluation metrics separately, plus a clearly labelled descriptive total for
all 30. Do not call all 30 an unseen test set. The references are already public in
the repository; runtime input separation reduces leakage but does not establish
that the model has never encountered the values. Freeze improvements on development
cases before evaluating all providers on the 24 held-out cases. After inspecting
hold-out failures, later tuning requires a new evaluation sample or an explicit
exploratory label.

## Autonomous access boundary

The agent receives only its input row. It must not read the sample, reference key,
evaluator manifest, dataset ID or known endpoint. Existing city-market IDs and
quarter remain legitimate question identifiers. Do not prefill provider queries
with a known source domain. Record generated queries, returned links, selected
sources and the discovery chain. A structured endpoint may be used after discovery
through returned links or retrieved documentation, with provenance retained.
A hard-coded DOT endpoint lookup is an assisted comparator, not autonomous success.

The evaluator reads `evaluator-manifest.json` only after an agent result exists.
Do not run the agent with unrestricted access to evaluator files or tools. Separate
agent inputs from scoring in the runner design, including model prompts and retry
context. This separation still needs implementation and testing in Part 2.

## Metrics and scoring proposal

Use Decimal and the preserved references. Absolute tolerances are 0.01 USD for fare,
0.01 passenger trips/day for traffic and exact distance. These are the existing
proposed tolerances, pending review; they may be strict for rounded secondary data.
Require the correct two city markets, year, quarter, attribute and units for
contextually correct retrieval. A numerically matching value from the wrong period
is not a correct business answer. Report numeric-only and context-aware correctness
separately when context is missing or mismatched.

Choose the first grounded candidate in recorded source order before consulting
the answer key. Acceptance is a policy decision; correctness is an evaluator
judgment. Keep both fields. Report per provider, split, condition and attribute:

- Candidate accuracy: correct contextual candidates / all assigned trials.
- Retrieval success: trials with at least one usable captured page or structured
  response / all assigned trials. Search HTTP success is a separate measure.
- Correct accepted rate and incorrect accepted rate, each over all trials.
- Accepted precision: correct accepted / accepted; undefined when accepted is zero.
- Unresolved rate: no accepted output / all trials; separately label conflicts,
  insufficient evidence and errors rather than hiding their causes.
- Mean and median elapsed seconds, including pacing; record stage timing separately.
- Search attempts, model usage, estimated cost and usage completeness. Do not call
  modeled rates actual charges. Report total cost and cost per correct accepted
  answer; the latter is undefined if none are correct and accepted.

Report numerators and denominators. Preserve failed and stopped trials. Do not
silently retry successes into a completed table or pool different code versions.

## Verification comparison

Preserve the Week 2 agreement rule as the comparison policy, adapted explicitly
for numeric context where necessary. A proposed authority-aware rule may accept
one exact original-publisher record only when identity, period, field, units and
supporting evidence match. Source authority is not established by a model's claim
or a domain suffix alone. Secondary copies of DOT are not independent witnesses.
The single-authoritative-source acceptance rule is NOT yet professor-confirmed.
Document it as an experimental policy and compare wrong acceptance as well as
coverage. Replay both verification policies over the same captured evidence when
possible, separating policy effects from changed search results.

## Proposed bounded execution

Initial pilot: six development cases through each of SerpApi and Brave (12 trials).
No third-service calls until selection and setup. Initial per-trial proposal:
maximum two query rounds, three source attempts and ten model calls; retain the
seven-second minimum spacing between model calls. Stop on authentication or quota
failure and preserve partial results. These caps require implementation in Part 2;
they are not assertions about existing safeguards. Fixed limits can reduce accuracy
and should be reported. Confirm remaining account quota and estimated batch cost
before live execution; no new subscription is authorized by this specification.

After development is frozen, compare all three services on the same 24 held-out
cases with rotated provider order and comparable budgets. Record the extra cost
of any additional development runs separately. Keep services' different retrieval
capabilities visible rather than forcing an unfair interpretation of equal calls.

## Business failure labels and evidence

Record wrong quarter, airport versus city-market mismatch, wrong units, different
fare definitions, unsupported rounding, unavailable structured data, blocked pages,
source revisions, absent independent evidence and current-value anchoring. Save
source URL, timestamp, response hash, quoted row or text, context fields, provider,
model, policy version and decision reason. Raw evidence and credentials remain in
ignored runs/; only reviewed public summaries may be published.

## Part 1 checks completed

Validated 30 unique records, exact answer/sample alignment, 10 tasks per field,
15 missing plus 15 controlled questionable inputs, six development plus 24 evaluation
cases, and no reference/source fields in the agent-input records. All questionable
values differ beyond tolerance. No source samples, pipeline code or version tags
were changed. These are data-contract checks, not live retrieval results.
