# Aviation regulations: pilot protocol

> Historical protocol for the initial Kenya development pilot. For the next phase, use [the commercial scope and extraction specification](commercial-scope-and-extraction.md), incorporating the later scope clarification. Statements below describe the protocol at preparation time.

Prepared 9 November 2026. Part 1: scope and source reconnaissance. No regulatory
agent trials have been run. This phase extends the existing project; it does not
replace the PEP or DOT experiments or change published versions.

## Research question and scope

Can the existing agent discover public historical aviation policy documents and
produce supported, reviewable regulatory-event records?

Countries: Kenya, South Africa and Nigeria. Primary window: 2009–2019 inclusive.
Track earlier agreements separately as background only when evidence supports
applicability during the window. An old signature alone does not establish that
an agreement remained applicable. Do not infer historical status from a current
list or treat a post-2019 entry into force as an event within the window.

Two topics per country: US bilateral air service agreements and amendments;
aviation safety oversight changes or restrictions relevant to international
services. Regional AU/AFCAC policy is contextual unless country applicability is
supported. Do not equate regional adoption with national implementation, FAA
oversight categories with individual airline safety, or an assessment with a ban.
The scope is our working interpretation, subject to professor feedback.

## Existing code inspection

- search_providers.py: reuse SerpApi/Brave discovery connectors and error handling.
  Snippets are leads, never sufficient evidence for accepted events.
- business_documents.py: reuse bounded PDF extraction and page markers. It has no
  OCR; encrypted, scanned, oversized or long documents can fail explicitly.
- business_agent.py: reuse retrieval safeguards and logging patterns. BusinessInput,
  BusinessClaim and numeric/context verification are DOT-specific and must not be
  reused unchanged for regulatory events.
- structured_retrieval.py: preserve as the DOT comparator; its schema checks and
  trust registry are not a general regulatory-document verifier.
- Existing model pacing and request budgets are useful patterns; confirm their
  integration in the next deliverable. No model/API upgrades are needed now.

## Pilot design and autonomy boundary

Use six development tasks (three countries times two topics), listed in
../../examples/aviation-regulations/pilot-tasks.json. Task inputs contain no
answers, event dates, document URLs or known agreement identifiers. The source
inventory is researcher reconnaissance, not an agent answer key. Known documents
may be used for separately labelled extraction-only tests; those are not evidence
of autonomous discovery. An official-source preference is disclosed guidance.

Compare SerpApi and Brave using the same generated initial queries, retrieval
limits and extraction/verification policy. Any adaptive follow-up queries and
query differences must be logged. Proposed first run caps: two searches, three
fetched candidate documents and six model HTTP attempts per task/provider, with
retries counted. Twelve trials therefore permit at most 24 searches, 36 candidate
documents and 72 model attempts; robots/redirect requests are logged separately.
These are proposed caps, not calls already made. Confirm account allowances before
live runs; stop on exhausted budgets/authentication failures. Do not enable paid
billing automatically. Cache only with provider terms respected and disclose
cache use in timing and cost reports.

This is development, not an unseen holdout. Freeze the revised procedure before
any later evaluation and identify overlap with development documents. A target of
6–12 events is illustrative, not an acceptance quota; zero events in a topic must
remain possible. Search failure does not prove that no regulation exists.

## Event schema and evidence

Final CSV columns: country, regulation_type, policy_description,
announcement_date, effective_date, source_url, supporting_evidence.
One row represents one country-event; a document can contain multiple events.
Use ISO full dates only where the day is explicit. Leave unknown full dates empty;
retain partial dates and date precision in the audit record rather than inventing
the first day of a month/year.

Separate audit JSON records event ID, country ISO3, agreement parties, event type,
signature/provisional-application dates, raw date wording, precision, date-specific
quotes, page/section, publisher and authority rationale, source retrieval time,
document hash, duplicate lineage, scope classification, unknown reason, conflicts,
and reviewer decision. A webpage publication date is not automatically an event
announcement or effective date. Preserve the original machine output separately
from corrections. Do not turn two copies of one announcement into corroboration.

Possible review outcomes: supported; supported event with unknown date;
needs human interpretation; conflicting evidence; out of scope; unsupported.
A single competent primary source can support an event; an official domain alone
cannot establish every claim. Literal quote matches check grounding, not truth.
Treat retrieved documents as untrusted data, never instructions to execute tools.

## Manual verification and evaluation

Review every proposed event against the full source and its date wording. Keep a
small researcher-selected document set for extraction checks; do not feed its
answers or URLs into the autonomous discovery condition. Prefer a second reviewer
for ambiguous cases; if unavailable disclose single-reviewer limitations.

Report counts and denominators, not percentages alone:
- Retrieval success: tasks obtaining at least one relevant readable document / tasks.
- Event precision: manually supported unique proposed events / proposed events.
- Date accuracy: correct machine dates / emitted dates, separately for announcement
  and effect; also report missing dates, partial dates and unsupported filled dates.
- Document-level recall only against manually enumerated events in a declared
  review corpus, never against all historical regulations on the web.
- Human correction/review rates, conflicts, inaccessible documents, failure codes.
- Elapsed time, request/token counts, retries, cache hits and estimated API cost;
  distinguish allocated usage cost from out-of-pocket charges/free credits.

Human-reviewed CSV quality is not machine accuracy. No calibrated confidence,
complete historical coverage or causal effect on connectivity is claimed.

## Deliverables and next gate

1. This protocol, source inventory and six blinded task definitions.
2. Regulatory extraction schema and small working demo, with offline failure tests.
3. Evidence/date verification and review workflow.
4. Paired provider pilot, corrected sample and transparent evaluation.
5. A 2–3-page report, reproducibility instructions and reviewed publication package.

Pause after each deliverable for discussion. Work stays local until release approval.
Keep credentials, private correspondence and raw runtime documents under ignored
local storage. Publish only reviewed results and permitted evidence excerpts.
No paid subscription is presently justified; identify the exact access gap first.
