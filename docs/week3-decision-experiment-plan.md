# Proposed experiment for cost aware retrieval decisions

Status: specification only. No new policy has been trained or evaluated and no
new API budget has been spent. Existing PEP and DOT results remain fixed.

## Research hypothesis

A policy using evidence provenance, context match and source dependence can improve
net utility relative to fixed-budget or confidence-only retrieval. Test this rather
than assuming that adaptive retrieval is always beneficial.

## First stage with controlled simulation

Use a finite horizon of up to three acquisitions and discrete candidate values,
including an unknown-other category. Specify synthetic source likelihoods and
costs explicitly. Include independent sources, sources sharing a copied parent,
a reliable source with a stale reporting period, wrong units, missing responses,
and a misleading official-source scenario. Label all outcomes synthetic.
Compare a myopic policy against exact finite-horizon dynamic programming under
the same known model. This checks decision logic; it does not validate web accuracy.
Use predeclared random seeds and paired episodes. Sweep error loss, abstention
loss, acquisition cost and dependence. A perfect-information oracle is only an
upper bound; it is not a feasible comparator with the same information.

## Second stage with new business records

Acquire new task/source trajectories outside the exposed 30 records, preferably
spanning periods and dataset families. Keep input fields free of answers and URLs.
Split by dataset family or related-source group to reduce leakage. Reserve separate
training, calibration and test sets before examining test outcomes. Choose sample
size using pilot variability and the precision required; do not claim a reliable
confidence model from the existing 30 observations.

Collect evidence under a declared exploration protocol so alternative retrieval
actions have observable outcomes. A saved trajectory only evaluates policies that
choose its available actions; it cannot reveal an unobserved alternative query.
Use prospective paired trials, randomized logging with appropriate support, or
explicitly limited replay. Missing action outcomes must not be treated as failures
or imputed from answers. Set a live-call and spend budget before acquisition.

## Policies and controls

- Stop after the first eligible candidate, using a declared acceptance rule.
- Fixed acquisition budget with the same final acceptance rule.
- Current DOT authority policy as a specialized comparator where applicable.
- Calibrated confidence-threshold policy.
- One-step expected-utility improvement policy with estimated transitions.
- Exact finite-horizon policy only in the controlled simulator.

Use the same tools, candidate-validation rules, initial evidence and cost accounting
where possible. Ablate provenance and dependence features separately. Keep Gemini
model/prompt and retrieval budgets fixed within each comparison. Count reasoning
calls as well as searches; adaptive planning is not free.

## Logged variables and scoring

Log candidate identity, unit, period, source publisher, citation/copy relationships,
grounding checks, calibrated confidence, available actions, selected action,
expected gain, actual API/token usage, response time, errors and remaining budget.
Ground truth is available only to offline evaluation. Model self-confidence is
not a calibrated posterior; fit and assess a separate estimator on reserved data.

Report net utility, incorrect acceptance per task, precision among accepted,
coverage/abstention, accuracy under declared tolerances, requests and money per
task, mean and p95 latency. Report Brier score and reliability plots for confidence;
ECE alone is unstable on small samples. Use paired uncertainty intervals with
resampling at the independent task/source-group level. AURC is secondary and
must account for changed retrieval trajectories when thresholds change.

Keep dollar costs and seconds separate. If utility combines them, declare weights
and sensitivity ranges. Predeclare U=0, error loss E=100 and abstention loss A=5
as one illustrative scenario, not an empirically justified business valuation.
Its terminal acceptance threshold is 0.95. Specify how dollar charges map to those
utility units; evaluate other valuations with Dr. Sibdari.

## Discussion decisions

Agree on the practical cost of a wrong value versus leaving it unresolved, the
next unseen dataset/period, acceptable acquisition budget, and whether the next
milestone is a simulator or a prospective adaptive-agent study. The existing
specialized success is a baseline, not proof of cross-domain autonomy.
