# Human review: workflow, responsibilities and interface

**Current interface:** use http://127.0.0.1:8765 and Submit to save directly to the
CSV. See [the updated instructions](review-interface-update.md). The portable HTML
and JSON-download instructions below describe the preserved earlier interface.

Open the generated local runs/aviation-review-interface-20261109/index.html in a
browser. No server or API calls are required. The generated file contains private
evidence and remains ignored. Only the builder/template belong in the repository.

## What has happened

1. Defined three countries and two topics from the professor's instructions.
2. For one Kenya safety task, Gemini generated queries shared by SerpApi and Brave.
3. Search connectors discovered URLs; the existing reader retrieved documents.
4. Gemini proposed events and dates; Python checked quotations and formatting.
5. Replayed three readable documents with improved whole-document section ranking,
   separate date types and status/scope checks; these were not new searches.
6. Added a shadow routing policy: would accept, needs review, unresolved. All current
   candidates need review. No verified enacted-event dataset has been produced.

This is an extension of existing components, not the unchanged old agent. The
successful DOT structured adapter is not being used to infer regulatory events.
Gemini proposes interpretations; deterministic checks do not prove legal meaning.

## Who does what

Automatic: query generation, discovery, bounded downloading, HTML/PDF text reading,
section selection, structured extraction, evidence linking, date/type checks,
source-role lookup, routing recommendations and review-card preparation.

Human interpretation: final versus draft status where evidence is ambiguous,
publication/issue/announcement/commencement meaning, applicability to research
scope, conflicting sources and evidence-backed corrections. A researcher also
validates shadow would-accept decisions before unattended acceptance is considered.

The agent should retrieve missing evidence when possible; a reviewer can request
more evidence rather than search everything manually. The interface records those
requests; it does not yet launch retrieval jobs automatically. Likewise it records
corrections but does not automatically import them into a verified dataset.

## Reviewing a candidate

Select a candidate tab. Each card shows a current machine value, a specific review
question and available quotations. Expand surrounding passages. Open the saved PDF
or official source when necessary. Corrected values require an evidence URL/page,
exact supporting passage and your interpretation. Keep unknown dates when evidence
is insufficient. Do not invent a full day/month from a title year.

Begin with cited passages and context, plus status/commencement/application sections.
You need not automatically read every page, but partial coverage cannot establish
absence of contrary provisions. For incomplete or ambiguous cases inspect further
sections or request evidence. Record whether you examined excerpts, the whole
source or additional sources. No false claim of whole-document review is needed.

Choose a field decision: keep, correct, still unknown/more evidence, outside scope.
Then record reviewer name, coverage, overall decision and reason. A correction is
an operation on a field; abstention/unresolved is a decision not to assert a value
or event. Neither is equivalent to deleting evidence or concluding no law exists.

## Saving

The interface tries to save drafts in browser storage, which may be unavailable
for local files or cleared by browser settings. Always use Download review JSON
before closing. Keep the downloaded JSON local (preferably under ignored runs/).
Resume it using the file picker. Downloads preserve original values through the
candidate/source identifiers and keep field decisions separate. They do not change
the original CSV, model outputs or GitHub. The reviewer is not assumed to be Jaideep;
existing assistant notes remain explicitly labelled and do not prefill approval.

The interface is a review aid, not a legal certification or independent evaluator.
No measured automatic-acceptance accuracy or human time savings have been established.
