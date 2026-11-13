# Staged US–South Africa trial

11 November 2026. One bounded revised development run. No subsequent retries or code changes.

## Results

| Measure | SerpApi | Brave |
|---|---:|---:|
| Searches | 2 | 2 |
| Parent document attempts | 0 | 3 |
| Attachments | 0 | 0 |
| Provider model attempts | 2 | 2 |
| Provider elapsed seconds | 15.813 | 13.133 |
| Extracted candidates | 0 | 0 |
| Verified events | 0 | 0 |

One shared query-planning call adds to four selection calls: five Gemini attempts total, no extraction calls. Counts remain within agreed limits. Provider timings include pacing but exclude shared planning; do not treat this tiny sequential comparison as a speed benchmark. Recorded token totals are in the local checkpoint summary. Cash charges were not independently checked; no purchases or billing changes were made.

## What happened

SerpApi returned results for both queries, but the selector chose none. Results included other countries' agreements, technical aviation cooperation material and broader leads. This is a selection outcome, not a search API outage, and it does not establish that every unselected lead was useless.

Brave discovered a result titled U.S.-South Africa Air Transport Agreement of July 23, 1996. The archive returned the known technical-error response and was marked ACCESS_ERROR. The observed title generated the second recovery query. Two more attempts targeted an agreement-list page and archive index; one failed retrieval and the other returned the same service-error response. The reserved second search was executed, but no substantive target agreement text was obtained. A title's date is a discovery clue, not a verified signing/effect date or proof of applicability during 2009–2019.

All fetched error responses were screened before extraction. No wrong-counterpart candidate or reconstructed signing date was produced in this run, but no extraction took place, so this is not a live validation of improved date extraction. The model did not select the earlier Chad PDF; deterministic counterpart rejection was not exercised live here.

## Comparison limits

The original run used eight Gemini calls and three searches total; this run used five calls and four searches. Both yielded zero verified target events. Shared initial queries were regenerated and differ from the first trial, while code and selection instructions also changed. Therefore this is a development comparison, not an isolated causal test of staged retrieval or provider superiority. The two providers shared initial queries within this run; Brave's recovery query was adaptive.

## Next discussion

Recovery still concentrated on the inaccessible State Department publisher. A next diagnostic should inspect the saved selection evidence and whether observed leads from other competent publishers could provide the instrument. Do not simply repeat the same archive searches or expand all six tasks. If a researcher locates a document separately, label that assisted discovery or an extraction-only test; do not count it as autonomous success. More precise access-failure reasons and selection reasoning would make this diagnosis easier.

Original results are in `runs/commercial-zaf-20261111-staged/`; the earlier run remains separate and unchanged. Saved downloaded-byte hashes were verified. No final event CSV or new human reviews were generated. Nothing was pushed to GitHub.
