# Live selection workflow trial

11 November 2026. One bounded development run using the saved readiness configuration. No code changes or additional trials were performed during this checkpoint.

## Results

| Measure | SerpApi | Brave |
|---|---:|---:|
| Search requests | 2 | 2 |
| Parent document attempts | 1 | 3 |
| Attachment attempts | 0 | 0 |
| Provider model calls | 2 | 2 |
| Provider elapsed seconds | 16.836 | 12.640 |
| Candidates extracted | 0 | 0 |
| Verified target events | 0 | 0 |

One shared planning call plus four selection calls: five successful Gemini attempts, 5,105 input tokens and 1,464 output tokens. No extraction calls occurred. Counts were within agreed ceilings; no new purchase or billing change was made. Cash charges were not independently verified. Timings exclude shared planning and are affected by pacing and sequential provider order.

## What was established

The live structured selection schema worked. Every supplied candidate received an indexed role and explanation, and selected/not-selected/deferred/attempted outcomes were saved. Downloaded bytes matched recorded hashes. Error-page screening prevented extraction from technical-error responses.

SerpApi selected no documents from the first query and selected the specific US–South Africa archive agreement from the second. That page returned the known technical-error response. Brave attempted the same agreement, an archive index and a current State Department index. Two returned technical-error pages; one failed with generic RETRIEVAL_FAILED. No substantive target agreement was read.

Brave's second selection requested three pages with only two parent slots left. The final selected directory is recorded as deferred, not silently lost. The run correctly stopped at its ceiling; deferral is not permission for an extra request. This run did not exercise carrying a first-stage deferred lead into the second stage.

## Policy problems now visible

- The model rejected an older archive agreement with the reason “Dated 1996, outside period 2009-2019.” This conflicts with the task's supported-prior-background allowance. Age alone does not establish relevance, but should not be the sole rejection reason when historical applicability is still being investigated.
- It labelled the ICAO database landing page unrelated because it was general. That is an overly narrow interpretation of discovery relevance; the page could be a navigation lead, though its actual usefulness/accessibility was not tested.
- Archive and primary-source roles were inconsistently labelled secondary leads. Roles are model judgements, not reliable authority classifications.
- Access-history context did not yield a successful different-publisher path. All attempted sources remained State Department pages. One failure on a host does not warrant automatically declaring all its pages inaccessible.

## Research conclusion and next discussion

Observability improved, but retrieval success did not. No extraction accuracy or provider-superiority claim is justified. The method and regenerated initial queries differ from prior runs; this is a development sequence, not a controlled single-factor comparison.

Stop repeating broad live trials for now. First resolve the background/navigation decision rules using offline cases. Separately diagnose the reader's generic failure on an observed official index, within permitted public access, before spending more search calls. A researcher-assisted source-access diagnostic must be labelled separately from autonomous discovery. Do not claim that the agreement does not exist or that it was in force in 2009–2019 from the title alone.

Raw evidence and selection explanations: `runs/commercial-zaf-20261111-selection/`. Earlier runs remain preserved. No new human labels, event CSV, expanded country tasks or GitHub push occurred.
