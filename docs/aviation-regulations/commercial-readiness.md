# Commercial trial readiness checkpoint

10 November 2026. Checkpoint B: offline implementation and readiness review. No live trial or publication performed.

## Changes

- Added `commercial_aviation.py`, an explicit commercial-event schema and prompt using the existing reader and evidence checks. Claim categories cover parties, routes, traffic rights, designation, capacity/frequency, pricing, restrictions, restoration, service scope and implementation. Each claim carries its own evidence. Lifecycle, event kind, period basis and implementation remain distinct.
- Added six separately labelled tasks in `examples/aviation-regulations/commercial-tasks.json`. Original pilot definitions and reviews are preserved. `aviation_agent.py --tasks` selects the new definitions. The `commercial_scope` switch defaults to false for previous callers, and commercial tasks cannot run through the legacy extraction path.
- Shared query generation receives the commercial scope. Section selection additionally ranks commercial provisions. No supplied answers, book passages or known agreement URLs enter discovery.
- The commercial audit checks extra citations, bilateral party evidence and commercial-consequence categories. Conditional/future/negative effect wording prevents automatic export of that effect date. These conservative lexical rules are not legal entailment or complete semantic validation.
- Every commercial candidate requires human review. A signature event is not forced through the old positive-enactment shadow-acceptance gate. Unknown effect is not treated as a false signature claim.
- Runtime manifests record the selected task and its input hash, source fingerprints, limits, shared planning attempts and provider usage counts. Retries count toward model limits.

## Proposed paired-run budget

| Resource | Limit |
|---|---|
| Shared query generation | 2 model HTTP attempts including retry |
| Model attempts per provider | 6 including retries |
| Total model attempts | 14 |
| Search requests per provider | 2 including attachment fallback searches |
| Parent document attempts per provider | 3 |
| Additional attachment attempts per provider | 2 |
| Model pacing | At least 7 seconds between attempts; inherited transient-error retry delay applies |

Thus the paired run permits at most four search requests, six parent document attempts and four attachment attempts. Redirect/robots requests are additional network operations, not additional provider searches. Model SDK retries are disabled beyond one attempt; the pacing wrapper owns one transient retry within the caps. Exhausted model caps can leave a partial trial, which must be reported. Provider order is fixed SerpApi then Brave and must be disclosed as a timing/order limitation.

## Validation performed

Offline suite: 166 tests run, 165 passed, one optional browser test skipped. Twelve new synthetic tests cover unknown effect after signature, fabricated commercial evidence, metadata, conditional effect, missing parties, absent commercial consequence, unresolved period, prompt/schema integration, live-runner dispatch with a fake provider, search cap, legacy-path rejection and empty-result handling. These tests establish code behavior, not historical extraction accuracy. No model/server response, real search, download or browser validation was performed in this checkpoint.

## Limits that remain explicit

- At most one event and four commercial claims per document, within the inherited 2048-token response limit. This can omit events; no complete inventory or recall claim is warranted. Real schema/output behavior still needs the bounded live trial.
- Model-supplied period classifications, lifecycle, implementation and claim meaning remain review questions. The current model does not reliably infer conditional satisfaction or historical continuity.
- Publisher registry is narrow; unknown publishers are flagged rather than assumed authoritative. Official-alternative PDF fallback therefore has limited coverage.
- Selection is bounded, not full-document model reading. OCR, comprehensive cross-source conflict resolution and automatic event deduplication are not added here. Duplicate event identification remains a review operation; repeated URLs are suppressed within a provider run.
- Existing review tooling contains Kenya-specific card preparation. New trial results include generic commercial review questions, but tailored cards and the reviewed seven-column CSV must be prepared at the review checkpoint. Do not use the old hard-coded Kenya card generator for these results.
- No automatic verified-event export or calibrated confidence is implemented. The detailed audit specification is broader than this first trial schema; provenance also lives in parent run records and manifests.

## Next gate

Review this checkpoint with Jaideep, confirm current free allowances, then run only ZAF-us_bilateral_air_services with the commercial task file. Do not launch all six tasks. Preserve the first results even if empty or unsuccessful. Diagnose before changing prompts or retrying. No subscriptions, billing changes or GitHub push are authorized by this readiness check.
