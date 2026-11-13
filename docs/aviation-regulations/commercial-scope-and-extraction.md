# Commercial aviation scope and extraction specification

Checkpoint A | 10 November 2026 | Design specification, not yet implemented or frozen for live evaluation

## Purpose and authority

Answer the original research question: Can an AI Web Agent reliably retrieve and structure historical regulatory information that is unavailable in conventional numerical datasets?

The original assignment remains the controlling scope: Kenya, South Africa and Nigeria; 2009–2019; US bilateral air-service agreements and safety restrictions/regulatory changes affecting international air connectivity. The subsequent commercial-aviation clarification narrows relevance. It does not authorize replacing the assignment with an unrestricted study of all African agreements.

Conceptual reference: Charles E. Schlumberger (2010), Open Skies for Africa: Implementing the Yamoussoukro Decision, World Bank, DOI 10.1596/978-0-8213-8205-9. Chapter 2 discusses commercial provisions; Chapter 3 distinguishes policy and operational implementation; Appendix A illustrates structured bilateral-agreement attributes. The book is researcher guidance, not an autonomous answer key or evidence of developments after its publication. Its historical interpretations must not be silently treated as current legal status.

## Task matrix and next trial

| Country | Topic A | Topic B |
|---|---|---|
| Kenya | US bilateral agreements and amendments | Restrictions and regulatory changes explicitly affecting international commercial services |
| South Africa | US bilateral agreements and amendments: first planned trial | Restrictions and regulatory changes explicitly affecting international commercial services |
| Nigeria | US bilateral agreements and amendments | Restrictions and regulatory changes explicitly affecting international commercial services |

Topic B is not automatically limited to US services; record the destination jurisdiction or route scope actually supported. The first new trial is US–South Africa agreements and relevant changes during 2009–2019. No known agreement identifiers, answer dates or source URLs enter its task input. The existing pilot task JSON remains historical until Checkpoint B deliberately updates and validates the runtime schema and prompts.

## Inclusion and exclusion rules

Include an identifiable commercial-policy event or provision whose country/service applicability and evidence are supported. Relevant categories include agreement signature or entry into force, amendments, designation/eligibility decisions, route or traffic-right changes, frequency/capacity conditions, fare-control provisions, and operating restrictions or restorations. Not every document contains every category.

For Topic B, require an explicit connection to commercial international operating eligibility, authorization or restrictions. An oversight assessment is not itself a flight ban; record only the consequences supported by the evidence. Do not require proof of a causal traffic effect to recognize a relevant policy event.

Exclude generic safety-management, maintenance, training, security or drone texts without the required commercial connection. A safety/security decision with such a connection can qualify. A new route announcement alone is operational context, not proof of a regulatory change. News and research reports can supply leads and attributed context; seek competent primary evidence for final regulatory claims, and flag cases where it is unavailable.

Keep intra-African agreements and regional liberalization initiatives as context unless they directly support an in-scope country event under Topic B. Do not add them as a new agreement-search topic without discussing scope. Regional adoption does not establish national implementation.

## Time and event unit

The primary unit is one country-specific event, with agreement parties, action and relevant date type recorded in its audit. Split materially different events (for example signature and later entry into force); do not turn every quoted provision or copied announcement into another event. Link related events by agreement/instrument ID and preserve provider provenance when deduplicating.

Classify records as in-window event, supported prior background, temporal relevance unresolved, or outside window. A pre-2009 agreement needs evidence of relevance/applicability during the window to enter background. A current list does not establish continuous historical applicability. Unknown effective dates are permitted if another supported event date establishes relevance; a year may support window classification without inventing a full date. If no evidence establishes temporal relevance, retain the candidate as unresolved.

Separate document publication, signature, announcement, provisional application and entry into force. Never substitute one for another. Extract explicit full dates as YYYY-MM-DD; store partial dates and original wording in the audit and leave the corresponding full-date CSV cell blank. Conditional commencement requires the condition and evidence of its satisfaction; otherwise effect remains unknown.

## Final CSV contract

The professor's seven columns remain unchanged:

| Column | Rule |
|---|---|
| country | Kenya, South Africa or Nigeria; other parties go in the audit |
| regulation_type | A defined commercial agreement/change/restriction category; avoid generic aviation labels |
| policy_description | Specific supported event, affected parties/services and material conditions; no inferred effect on traffic |
| announcement_date | Explicit announcement date only; blank means unknown |
| effective_date | Explicitly supported effect date only; blank means unknown |
| source_url | Best supporting source, with other sources in the audit |
| supporting_evidence | Short exact passage(s) and page/section locations supporting the claim; distinguish separate excerpts |

Export supported events with unknown dates without calling the dates verified. Keep prior background, unresolved candidates and exclusions in clearly separate outputs. Publication-only records must be labelled as publication events, not enactment or operation. The Kenya pilot's limited publication record is not automatically promoted to the commercial-event dataset.

## Supporting audit specification

| Group | Fields to preserve |
|---|---|
| Identity | candidate/event ID, task ID, country, counterpart countries, instrument/agreement ID, parent event and duplicate lineage |
| Commercial content | provision category, rights or restrictions, previous/new condition when supported, passenger/cargo, scheduled/charter, carriers/routes, exceptions and territorial scope |
| Lifecycle | proposed/signed/effective/amended/suspended/restored/unknown as evidence supports; implementation evidence separate from legal status |
| Dates | date type, normalized date or null, raw wording, precision, supporting passage, conditions, period classification and unknown reason |
| Evidence | claim-to-passage links, document URL, publisher role, page/section, document hash and retrieval time; primary/secondary role relative to claim |
| Coverage | PDF/text availability, selected sections, omitted coverage, fallback source and unconfirmed edition equivalence |
| Verification | grounding result, semantic support, applicability, temporal support, conflicts, routing reasons and unresolved questions |
| Review | original proposal, reviewer decision, corrected fields, correction evidence, reviewer identity, assistant assistance and review time |
| Experiment | configuration/code/prompt identifiers, provider, actual queries, request and retry counts, timing, tokens/cost basis, cache use and failures |

These are proposed requirements; existing code does not yet implement every field. Empty/unknown and not applicable must remain distinct. No numerical confidence is inferred from authority labels or agreement between copied sources.

## Verification and human review

Check literal grounding, meaning, competent publisher for the claim, country/service scope, date type, final status and conflicting evidence separately. Matching text does not prove the extracted description. One suitable primary source can support a claim; two copies are not independent confirmation. Search snippets and catalogue metadata are discovery leads, not sufficient proof of substantive agreement provisions.

Route candidates as supported recommendation, needs review, unresolved or out of scope. During this small evaluation, review every proposed event, including positive recommendations, to measure false acceptance. Start at cited passages and surrounding conditions; inspect additional document sections when necessary. Preserve original outputs and record corrections separately. Assistant checks are not an independent second human review.

## Comparison and evaluation rules

Use the same generated initial queries, extraction method and comparable caps for SerpApi and Brave. Save each provider's original outcomes separately before combining sources. Disclose adaptive queries, attachment/fallback searches, cache usage and human assistance. Do not rerun until a favourable outcome appears. A method modified using this trial creates development overlap, which must be labelled in later evaluation.

Report relevant readable-document retrieval per task-provider trial; supported original unique event proposals divided by all original unique proposals; correct emitted dates divided by emitted dates for each date type; missing dates, correction burden and failure-stage counts. Zero proposals gives undefined proposal precision, not 100 percent. Evaluate recommended acceptance against human support separately. Record all request failures/retries and distinguish free-credit consumption from cash charges. Corpus recall needs a declared reviewed reference collection; do not claim web-wide completeness. No new accuracy values or provider rankings are established by this specification.

## Checkpoint B readiness requirements

1. Map these requirements onto current code, schema, prompts and review/export tools; identify gaps before edits.
2. Implement only necessary changes with explanatory comments; preserve earlier PEP/DOT and Kenya development results.
3. Add meaningful checks for metadata mistaken for provisions, wrong date meanings, assessment mistaken for ban, ungrounded rights, conditional effect, unknowns, duplicates and access failures.
4. Verify request accounting for shared query generation, retries, attachment downloads and fallback searches. Set actual caps after code inspection; earlier proposed caps are not assumed enforced.
5. Confirm available free allowances before live execution; retain conservative Gemini pacing below the stated 15-RPM ceiling. Do not enable billing or purchase services.
6. Save code/prompt/configuration fingerprints and the final task input, then discuss readiness with Jaideep before live calls.

## Status and preserved history

Checkpoint A updates the research design only. No runtime code, original task definitions, raw evidence, human labels or published release is changed. No live search/model calls or GitHub publication are performed. The Kenya pilot remains useful development evidence but does not complete Topic B under the clarified commercial scope. This document takes precedence for the next phase over the earlier broad pilot interpretation.
