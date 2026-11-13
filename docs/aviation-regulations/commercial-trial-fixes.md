# Commercial trial fixes and offline validation

11 November 2026. Revised method: commercial-aviation-dev2. The first live trial remains unchanged; no revised live run has occurred.

## Changes

1. Short service-error responses are classified as ACCESS_ERROR, saved with provenance and counted against the document budget. They are not sent to Gemini for extraction. Detection requires a narrow error-page pattern; ordinary regulatory uses of “forbidden” are not rejected.
2. Result selection explicitly warns against other bilateral counterparts. A deterministic gate recognizes explicit two-government cover headings: when the target country is paired with a non-US counterpart, the document is labelled OUT_OF_SCOPE before extraction. Unknown layouts are not guessed; they continue to extraction/review. The same gate applies to the final text after attachment substitution. This is a layout-specific safeguard, not universal party recognition.
3. The extraction prompt requires unknown/illegible dates to remain null and forbids reconstruction of missing day/month values or unsupported dates in descriptions. Date audits now expose a validated-date view that blanks failed dates while preserving proposed values and reasons. Descriptions with date issues are explicitly marked for review; no automatic rewriting hides the original error.
4. All commercial candidates remain review-first. Bounds remain two searches, three parent-document attempts, two extra attachments and six model attempts per provider, plus two shared planning attempts. Failed attempts are not refunded. No extra access attempts or larger search budget were silently introduced.

## Actual verification

171 tests ran: 170 passed and one optional browser test skipped. New tests cover error-page false positives, correct versus incorrect counterpart headings, skipping unnecessary model calls, preservation versus withholding of unsupported dates, and retention of failed attempts in budget counts. A valid US heading initially exposed a leading-article normalization bug; it was fixed and the suite rerun successfully.

An offline replay of all four saved document records classified three technical-error responses as ACCESS_ERROR and the South Africa–Chad agreement as OUT_OF_SCOPE. Reassessing the original proposal leaves the proposed signing date in the audit but withholds it from validated dates. Hashes of every file in the original trial were unchanged. The replay used saved text and the original proposal, not fresh Gemini extraction or network requests.

## What this does not prove

The fixes avoid wasted extraction on these error pages and a known explicit mismatch. They do not recover inaccessible agreements, establish general party/date accuracy or improve measured live retrieval success yet. Unknown heading layouts still require review. The narrow publisher registry still flags unclassified hosts, including the observed ICAO subdomain; no authority label is silently upgraded. Section selection, one-event-per-document limits and incomplete historical coverage remain.

## Next discussion

Review this checkpoint, then authorize a separately labelled bounded rerun if desired. Keep the original trial as the baseline. The same document ceiling may still be exhausted on inaccessible results; any proposed budget reallocation or official-source fallback change should be recorded as another method change rather than claimed to be already tested. Do not expand the other country-topic tasks until this result is discussed.

Local evidence: `runs/commercial-fixes-20261111/offline-replay.json`, `test-results.txt`, and `configuration-snapshot.json`. No API calls, purchases, GitHub push, accepted events or new human labels were produced by this checkpoint.
