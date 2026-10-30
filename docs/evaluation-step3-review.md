# Deliverable 3 — interpretation and discussion

Completed on **2026-10-28**. This is the
performance-evaluation deliverable; business dataset preparation is documented
in business-dataset-step4.md.

## Main finding

The specialized baseline handled this PEP sample reliably, while the autonomous
pipeline still has major discovery and corroboration limitations. The Brave
configuration retrieved at least one page for every observation and usually
extracted a correct candidate; it produced agreement on only six observations.
The SerpApi configuration frequently returned unrelated candidates and then
failed to recover within its query policy. This is not evidence that SerpApi is
universally inferior or Brave universally best.

| Configuration | Correct candidate | At least one page retrieved | Correct accepted output | Mean time, paced | Paid-tier cost scenario |
|---|---:|---:|---:|---:|---:|
| Original baseline | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 6.75 s | $0.5153 |
| Autonomous + SerpApi | 1/20 (5%) | 1/20 (5%) | 0/20 (0%) | 25.60 s | $0.8207 |
| Autonomous + Brave | 18/20 (90%) | 20/20 (100%) | 6/20 (30%) | 34.97 s | $0.2193 |

**Baseline advantage:** every baseline record used the known canonical URL
fallback, rather than a matching SerpApi result. Its final acceptance also uses
an official-answer oracle. The 100% score therefore does not demonstrate
successful autonomous source discovery or independent verification.

**Autonomous accuracy definition:** the first mechanically grounded candidate is
compared to the frozen reference, even if the system abstains or flags conflict.
This is diagnostic candidate accuracy, not the success rate of automatic
multi-source verification. Brave's accepted-correct rate is 30%, not 90%.

**Timing and cost:** times include the seven-second minimum spacing between model
calls, so they cannot rank raw provider speed. The complete paced run made 85
logical search attempts and 193 model calls. Its paid-tier scenario totals
**$1.5553**, before credits/free quotas and without account-billing confirmation.
All 193 model calls returned usage. See the protocol for rates and assumptions.

## Observed failures

1. **Query ambiguity / irrelevant discovery.** Queries such as `PEP 841 title`
   produced unrelated legal pages in the SerpApi configuration, while queries for
   `PEP 776` produced flight-related results. Selection rejected irrelevant pages.
   This protects against unsupported extraction but does not satisfy the task.
2. **Rejected reformulations.** Eight SerpApi-configuration trials ended in
   query-generation `ValueError`. Replaying validation against the recorded
   candidates confirmed each retry introduced a domain absent from prior results.
   The query guard behaved as implemented; recovery from that rejection is poor.
   All 32 SerpApi and 33 Brave autonomous search calls returned successfully.
3. **Insufficient corroboration.** Each autonomous configuration returned
   INSUFFICIENT_EVIDENCE on 12 observations. In Brave runs many of these contained
   a correct single-source candidate, but not enough usable evidence for agreement.
4. **Title prefix inconsistency.** The first Brave candidates for PEP 841 and
   PEP 818 included their PEP identifiers. Under the declared strict scoring these
   are the two incorrect candidates. They are not necessarily wrong underlying
   document identities; changing the scorer afterward would hide the issue.
5. **Conflicts need semantic/context review.** Brave produced two conflicts:
   PEP 467 differed by a `PEP 467:` prefix. PEP 818 combined a prefixed title, the
   reference title, and a different discussion heading, `Upstreaming the Pyodide
   JavaScript Foreign Function Interface`. This can reflect title/version/context
   differences; the run does not establish a factual contradiction. None of the
   conflicts was automatically accepted.
6. **Related pages are not independent witnesses.** Official pages, repositories,
   and discussions can share an origin. Agreement does not establish independence.

## Quota incident and corrective evaluation procedure

The initial unpaced run was interrupted after 48 saved trials (16/configuration):
5 ACCEPT, 39 ERROR, 4 INSUFFICIENT_EVIDENCE. Its autonomous records explicitly
contain 27 Gemini HTTP 429 responses. Do not infer that every error was a 429;
the original baseline error records do not carry HTTP codes.

The user confirmed dashboard limits of 15 RPM, 250,000 input TPM, and 500 daily
requests; reported usage reached 15 RPM while token and daily limits were below
capacity. The evaluator was then changed to pace model requests and stop after a
429, preserving the failed run. The second run is separate, not a set of successful
retries substituted into the first run. The pipelines and benchmark were unchanged.

The paced run completed 60/60 trials from **18:17:44 to 18:40:11 America/New_York**,
with no recorded model HTTP errors. The initial saved trials carry a separate
**$0.5938 cost scenario**; failed-call usage and the interrupted in-flight trial
are incomplete, so this is not a total invoice. Raw incident artifacts remain in
`runs/evaluation-deliverable3-20261028/`; the completed experiment is in
`runs/evaluation-deliverable3-paced-20261028/`.

## Verification and reproducibility

- **60 tests passed**, including the real local Chromium test, scoring denominator
  checks, first-candidate selection, missing-usage costing, the 429 safeguard,
  partial-report labelling, and exclusion of raw runtime payloads from reports.
- Dependency check: no broken requirements.
- Exactly 60 unique observation/configuration pairs, 20 per configuration.
- All **55/55** captured evidence hashes match their saved records.
- Pipeline/evaluator hashes still match the completed run manifest.
- No per-observation pipeline tuning during the paced run; errors remain counted.
- Credentials and raw run/evidence outputs remain ignored by Git. Public report
  content is limited to reviewed metrics, public benchmark fields and diagnostics.
- Source files `agent.py`, `autonomous.py`, and `multisource.py` are unchanged by
  this deliverable. Windows/Linux execution and fresh installation were not
  repeated; the actual local environment was macOS with the existing pinned setup.

Reproduction and metric definitions: [evaluation protocol](evaluation-step3.md).
Full tables/failure inventory: [generated findings](evaluation-step3-findings.md).
Machine-readable reviewed results: [evaluation-results.json](evaluation-results.json).
