# First commercial trial results

11 November 2026 | Checkpoint C | One development task, no reruns or method changes

## Task and method

Task: US–South Africa bilateral air-service agreements and relevant changes in 2009–2019, with supported earlier background kept distinct. The pre-run code fingerprints matched the readiness snapshot. Both providers received the same two Gemini-generated initial queries. Neither received known agreement identifiers, answer dates or researcher-selected URLs.

The initial queries were “United States South Africa bilateral air transport agreement text commercial flights” and “South Africa United States open skies air services agreement department of transportation”. They omitted explicit period terms; whether adding them helps discovery is a later test, not an established cause of failure.

## Actual results

| Measure | SerpApi | Brave |
|---|---:|---:|
| Search requests | 2 | 1 |
| Parent document attempts | 1 | 3 |
| Additional attachment attempts | 0 | 0 |
| Provider-specific Gemini attempts | 3 | 4 |
| Provider elapsed seconds | 20.894 | 30.003 |
| Original machine candidates | 0 | 1 |
| Verified target events | 0 | 0 |

One additional Gemini call generated shared queries: eight total attempts, all successful at the API level, with no retries. Recorded usage totals are 11,581 input tokens and 1,037 output tokens. The API successfully responding does not establish that its content is correct. Provider timings exclude shared planning and are affected by sequential provider order and common pacing. No monetary charge is asserted without billing verification; no billing changes or purchases were made.

## Failure diagnosis

1. **Document access:** Both providers found a US State Department archive link, but it returned only a 153-character technical-difficulties/forbidden page. Brave encountered the same response at a second archive URL. The reader labelled these pages READ because it obtained text. That label incorrectly suggests substantive document access. The extractor appropriately returned no events from those error pages.
2. **Relevance:** Brave's third document was an ICAO-hosted South Africa–Chad agreement. The downloaded text explicitly identifies those parties. It is not relevant to the US bilateral task. The model nevertheless proposed it as a candidate. The audit raised BILATERAL_PARTIES_REQUIRE_REVIEW, but the pipeline did not classify the explicit counterpart mismatch as out of scope.
3. **Date extraction:** Gemini proposed 2017-05-21 as the signing date. The cited text contains a poorly extracted handwritten dating line and does not substantiate that precise date. The date audit flagged DATE_NOT_EXPLICIT_IN_QUOTE and DATE_TYPE_NOT_SUPPORTED. The proposal remains unverified; no replacement date is inferred.
4. **Authority registry:** The exact ICAO subdomain was unclassified by the narrow registry. This is a registry-coverage limitation, not evidence that the site is illegitimate. Adding a role would not make the wrong-country agreement relevant or fix the date.
5. **Budget interaction:** Brave stopped after its three parent-document attempts, so its second planned query was not executed. This follows the frozen limit; the trials had the same ceilings, not identical numbers of executed searches. Two error pages consumed document slots.

Brave selected 23,935 of 47,888 extracted characters from the PDF. This was section-based model reading, not examination of every page. The genuine PDF is an access success but not target-task retrieval success. No PDF attachment fallback was exercised in this trial.

## Interpretation

Neither workflow produced a supported target event in this run. This does not show that no US–South Africa agreement exists. It also does not justify declaring one provider superior. The main observed issues concern archive access, counterpart relevance and unsupported date reconstruction. Evidence checks prevented automatic acceptance, but unnecessary review burden remains.

This is assistant inspection of saved run evidence, not a completed independent human-label evaluation. Original machine proposals remain unchanged. Saved raw document hashes were checked against all four download records; the technical-error responses share the same hash.

## Proposed next checkpoint for discussion

Before another live call, implement and offline-test a narrow detector for service-error pages, require explicit counterpart matching for US bilateral extraction, and ensure unreadable date wording remains unknown. Preserve failed requests in the budget; do not silently refund limits. Evaluate whether the next separately labelled configuration should reserve capacity for another query or use an observed official alternative. Inspect candidate-selection evidence before changing search strategy. Any new run is a revised development trial, not a replacement for these first results.

Raw evidence, model usage, original results and a compact summary are preserved locally under `runs/commercial-zaf-20261111-first/`. No corrected event CSV, live rerun, additional task, code fix or GitHub push was performed at this checkpoint.
