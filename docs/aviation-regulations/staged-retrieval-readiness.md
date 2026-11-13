# Staged retrieval readiness

11 November 2026. Offline implementation only; no revised live trial yet.

## Revised sequence

1. Execute the first shared initial query and select observed results.
2. Attempt at most two parent documents from that search, preserving one of the three document slots for the next search.
3. If a document or linked attachment was inaccessible and the observed result has a usable title, construct a bounded recovery query from that title plus task scope. Strip URLs and query operators. The title is a discovery lead, not verified evidence.
4. Use the second search slot for that recovery query; otherwise retain the second shared initial query. Record both the planned query and actual query, the observed title, failed source and reason.
5. Attempt remaining parent documents and follow bounded observed attachments. Keep the existing access-error, counterpart and date checks. Preserve source provenance and do not assume an alternative has identical contents.

Commercial runs now use this central recovery path instead of the earlier inline attachment-search fallback. Observed attachment downloads still operate within their original limit. Legacy runs retain their previous behavior.

## Bounds and comparison

Limits remain two searches, three parent-document attempts, two extra attachment attempts and six model HTTP attempts per provider; shared planning has two attempts, giving fourteen model attempts overall. Failed requests count. No third query, budget refund, extra model query-generation call or automatic repeated run is introduced.

Both providers still start with shared initial queries, but actual recovery queries may differ because their retrieved titles/failures differ. Compare the two adaptive pipelines under shared ceilings; do not describe this as an identical-query experiment. A suitable title, accessible alternative or useful next result is not guaranteed. The first failed usable title is chosen deterministically; better title selection and document edition matching remain limitations.

## Offline evidence

175 tests run: 174 passed; one optional browser test skipped. Four new tests cover recovery from observed titles, no recovery for missing titles/readable sources, removal of URLs/operators, and reserving a second search/document opportunity when the first search returns three candidates. The synthetic integration test records exactly two searches and three document attempts, with original and replacement query provenance.

These tests establish allocation and logging behavior, not successful retrieval of a real agreement. Earlier live results remain the baseline. No new candidate, accepted event or historical date is asserted.

## Next checkpoint

After discussion, run the single US–South Africa task once under this revised configuration and preserve it separately. Compare relevant-source access, exclusions, candidate evidence and resource use with the original trial. Do not expand all tasks or publish until reviewed.
