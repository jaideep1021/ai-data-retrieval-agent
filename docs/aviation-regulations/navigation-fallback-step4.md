# Step 4: offline navigation fallback

12 November 2026. No network or model calls.

Commercial selection now supplements selected indices with observed candidates labelled official_navigation, preserving their relative order. The existing two-search/three-parent-attempt limits still apply; excess selected candidates are deferred. Already-attempted URLs are not retried. Exact origins with ROBOTS_UNAVAILABLE_OR_DENIED in this run are deferred. SERVICE_ERROR_PAGE downranks that origin but does not prohibit other paths. Parser failures do not downrank publishers. Different subdomains are not grouped together. Original model output and deterministic fallback decisions are logged separately.

Replay of saved content-links trial selections:
- SerpApi search 1: [0] becomes [0,4,5], retaining ICAO and DOT navigation leads.
- SerpApi search 2: [2,8] unchanged.
- Brave search 1: [0] becomes [0,6,7], retaining directory leads.
- Brave search 2: [1,2] becomes [2,6,1], moving the known service-error origin behind alternatives.

These are separate static replays using historical access context, not a counterfactual full run: changed first-stage retrieval would change subsequent evidence. No claim of increased retrieval success is justified. Original search/model outcomes remain unchanged. Evidence: runs/navigation-replay-20261112/results.json.

Validation: 193 tests run, 192 passed, one optional browser test skipped. New tests cover navigation queuing, service-error downranking, exact-origin robots deferral, no repeated URL, parser-failure distinction, and no inclusion of unrelated candidates. git diff --check passed.

Limits: labels remain model judgements; a navigation lead may still be irrelevant. Candidate and parent limits can prevent following all leads. This policy is run-local, not a persistent publisher blacklist. No live API trial or push occurred.
