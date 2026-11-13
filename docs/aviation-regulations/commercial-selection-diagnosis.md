# Offline source selection diagnosis

11 November 2026. Inspection of stored search results and code only. No new website access, API calls or changes to the running method.

## Findings supported by the saved records

SerpApi returned 18 results over two searches. Many clearly concern other countries, technical cooperation or material outside the target period. Selecting none is not necessarily a failure for those items. However, the second result set includes a State Department air-transport media-notes page and a University of Pretoria research document. These may provide discovery leads, although neither is established as the correct agreement or sufficient primary evidence. The CAAC-hosted PDF's actual parties cannot be determined confidently from its generic snippet alone; its host must not be treated as proof of the parties.

Brave returned 20 results over two searches. It identified a specifically titled US–South Africa agreement in a State Department archive. Access failed. Other observed results included the US Department of Transportation Air Service Agreements page in the first query and the ICAO Database of World's Air Services Agreements page in the recovery query. Neither was attempted. They are potential navigation routes, not verified alternative copies. No assumption is made about their accessibility, fees, relevant records or ability to resolve historical applicability.

The three Brave attempts all targeted state.gov or its archive subdomains. Two returned identical service-error text; one failed with only a generic RETRIEVAL_FAILED reason. Recovery changed the query but did not achieve publisher diversification. Error screening worked after retrieval; selection was not given a structured record of preceding publisher access failures.

## Logging and allocation gap

Selection returns indices only. The run stores fetched documents, but not the full candidate list actually passed to selection (which can include previously observed links), all selected indices, or concise selection reasons. On the first search only the first two selected indices are attempted. A third selected lead is discarded rather than queued for the second stage. It is therefore not possible to reconstruct whether an unvisited result was rejected or selected but truncated. Do not invent retrospective model reasoning. SerpApi's empty document list supports that no indices were selected in that completed run, but its reasons remain unknown.

## Recommended targeted changes

1. Save the selection input, selected indices and short evidence-based reasons; distinguish rejected, deferred and attempted results. Reasons are model explanations, not proof of relevance.
2. Classify leads as candidate instrument, official navigation/index, secondary discovery lead, clearly unrelated or uncertain. Permit a navigation page to help find a document without treating that page as substantive regulatory evidence.
3. Carry selected but unattempted leads into the next bounded stage. Do not silently discard a useful third choice when reserving a document slot.
4. Give selection structured access history and prefer another observed publisher when one publisher's pages have repeatedly failed. Avoid a blanket ban on a whole publisher after one failed page. No invented URLs or hard-coded agreement answers.
5. Record safe specific access-failure codes where available; preserve original evidence and existing request ceilings. No bypass of access restrictions.
6. Test these decisions with synthetic data and saved result sets before another live call. Reviewing saved sets is development reuse, not an independent evaluation.

## Boundaries and next decision

The diagnosis identifies unvisited leads and missing observability, not a recovered agreement. There is still no supported target event or demonstrated live retrieval improvement. A successful title hit is not evidence of the signing date, current status or applicability in 2009–2019. Do not convert search snippets into verified records to fill the dataset.

After discussing the changes, implement selection logging and deferred-lead handling first, then assess whether a single further bounded trial is justified. A researcher-located source must remain labelled assisted discovery or extraction-only, separate from autonomous performance. Do not expand all tasks or repeatedly rerun the inaccessible archive.

Evidence inspected: local `runs/commercial-zaf-20261111-staged/serpapi/result.json`, `brave/result.json`, `model-calls.json`, and `aviation_agent.py`. All original run files remain unchanged. No GitHub push occurred.
