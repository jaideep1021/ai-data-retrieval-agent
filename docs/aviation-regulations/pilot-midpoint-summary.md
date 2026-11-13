# Aviation regulatory pilot: midpoint summary

Prepared 10 November 2026. Local development checkpoint, not a completed six-task evaluation.

## Objective and scope

Extend the existing agent to discover and structure historical aviation regulations for Kenya, South Africa and Nigeria during 2009–2019. The two areas are US bilateral air-service agreements and safety/regulatory changes relevant to international connectivity. This creates six country-topic combinations. Only the Kenya safety task has been explored so far; even that historical inventory is incomplete.

## Six pilot checkpoints

1. Defined task inputs, source guidance, date meanings and evidence requirements.
2. Demonstrated autonomous Kenya discovery with Gemini-generated queries and SerpApi/Brave, without supplied document URLs or reference answers.
3. Improved document-section selection, quotation checks, date separation and source-role checks. Tested on saved documents; this replay is not fresh autonomous discovery.
4. Added PDF attachment/fallback retrieval and a local human-review form. The researcher reviewed three section-based candidates; corrections and source snapshots remain auditable.
5. Checked submitted corrections against saved PDFs and exported one limited reviewed record, retaining unknown dates and excluded/unresolved decisions.
6. Consolidated findings and proposed the next evaluation. This document closes the development-pilot summary checkpoint, not the professor's full deliverable.

These checkpoints describe the development sequence; the original protocol groups deliverables differently. They do not represent six completed country-topic tasks.

## Candidate outcomes

| Candidate | Disposition | Evidence and remaining gaps |
|---|---|---|
| Kenya Safety Management Regulations, 2018 | Limited reviewed publication/instrument record | Gazette header supports 4 May 2018. Regulation 18 states that the 2015 regulations are revoked. Separate document date is 26 March 2018. Announcement and effective dates remain unknown; a connectivity effect is not demonstrated. |
| Security regulations | Unresolved, within researcher-approved scope | Incomplete dating line and unconfirmed final status prevent a dated enacted-event claim. |
| Unmanned aircraft regulations | Excluded from the current airline-connectivity scope | Researcher scope decision; draft indication/final-status uncertainty remains recorded. Exclusion does not mean the source is false. |

There is one limited reviewed record and zero fully verified effective-dated events. Unknown effective dates do not automatically invalidate an otherwise supported event: the issue here is precisely which event and legal-status claims the evidence supports. Publication, signature/document date, announcement and commencement must stay distinct.

## What we learned

- Search results can lead to repository metadata rather than the actual instrument. The agent now follows observed PDF links and can search for official alternatives when attachment access fails. An alternative is not assumed to be the identical edition.
- Reading only the first 24,000 characters can omit decisive evidence. Document-wide section selection exposed an incomplete dating line near the end of a 96-page PDF. Selected sections still do not guarantee full-document examination by the model.
- Official hosting helps identify a publisher but does not prove final legal status, dates or applicability. A regulator may host a draft.
- Exact quotation checks identify grounding problems but cannot prove the whole claim. PDF heading order and hyphen spacing can also cause mechanical mismatches.
- The review interface preserves researcher corrections separately from original machine proposals. Current triage is a development aid, not a validated autonomous acceptance policy.

## Human review boundary

The agent handles query generation, search, bounded downloads, text extraction, candidate structuring, evidence checks and review routing. Human judgement remains needed for ambiguous status, date meaning, research scope, conflicts and applicability. For this small research evaluation, inspect every proposed event, including anything the system would accept, so false acceptance can be measured. In a future deployment, reduced review would require validation and a documented sampling policy; it is not established here.

## What the pilot does not establish

No population accuracy, provider superiority, full historical recall, causal connectivity effect, calibrated confidence or learned stopping policy is claimed. Three reviewed development candidates are not an independent test set. Researcher-corrected output quality must not be reported as original machine accuracy. No new API calls were made for the Step 5 validation or this summary.

## Proposed expansion after discussion

1. Confirm with Dr. Sibdari whether aviation security belongs within scope and whether publication/instrument records with unknown commencement should accompany the final event sample. Clarify that the study needs relevant regulatory changes, not proof of causal impact on connectivity.
2. Freeze the task inputs, extractor, review rules and request caps before new trials. Keep Kenya development cases labelled separately.
3. Use the same initial generated queries and retrieval limits for both providers. Log any adaptive/fallback queries, failed requests, caching and human assistance. Check remaining free allowances before running; do not buy services or switch billing automatically.
4. Cover the five untested country-topic combinations and rerun Kenya safety only if needed for a consistent paired comparison. That would be 12 provider/task trials for the complete six-task matrix, not 12 trials already completed. The original proposed ceilings were 24 searches and 72 model HTTP attempts; verify that attachment/fallback and retry accounting obey these bounds before execution.
5. Review all proposed events, retain unknown dates, record disagreements and deduplicate events without counting copies as independent corroboration. Any researcher-selected reference documents stay outside autonomous discovery inputs.
6. Report relevant-readable-document retrieval by task, supported unique events over proposed unique events, date correctness and missingness separately, human correction burden, failures, time and actual request/token usage. Compare providers only on matched trials and disclose development overlap. Assess recall only against a defined reviewed corpus, never all regulations on the web.
7. Prepare the requested CSV, reproducible code/results and 2–3-page report. Review the publication package with Jaideep before any GitHub push.

## Evidence trail

Earlier findings: [autonomous demo](step2-findings.md), [section-selection diagnostic](step3-findings.md), [verification guide](verification-guide.md), and [review interface](review-interface-update.md).

Local private artifacts remain under `runs/aviation-pilot-reviewed-20261110/`: `step5-summary.md`, `reviewed-pilot.csv`, and `validation-audit.json`. The audit records three matching reviewed-PDF hashes, seven matched passages and the incomplete security dating line. Original human labels remain unchanged. These runtime files are not included in Git publication.
