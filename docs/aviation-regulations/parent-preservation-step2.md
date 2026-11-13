# Step 2: parent-document preservation before parsing

11 November 2026. Offline implementation checkpoint; no network, search or Gemini calls.

## Behavior
BusinessRetriever.fetch_document accepts an optional preserve_raw callback. After an HTTP 200 response completes under existing reader limits, the callback receives response bytes, final URL and content type before any PDF/HTML/JSON parsing. Aviation's caller owns the evidence directory and writes document-N.bin, then records raw_file, raw_sha256, bytes, source_url and content_type. Existing callers that omit the callback retain their API behavior.

A subsequent parser failure becomes READ_FAILED with the safe reason code. A retrieval failure remains FETCH_FAILED and does not reuse a previous response. Recovery accepts READ_FAILED alongside FETCH_FAILED and ACCESS_ERROR. Original historical run files are not relabelled. Evidence write errors occur before metadata is marked preserved; they do not count as preserved parser failures.

## Validation
184 tests run: 183 passed, one optional browser test skipped. New offline runner tests verify byte content, hash, byte count, saved JSON metadata, absence of extracted text/events after PDF_HAS_NO_EXTRACTABLE_TEXT, continued recovery eligibility, and no stale-byte artifact after a download failure. Existing fake readers were updated for the optional callback keyword. git diff --check passed.

## Limits and next step
No OCR, counterpart-regex changes, navigation policy changes, live trial or GitHub push. Existing completed downloads only are preserved; interrupted/oversized/non-200 responses are not retained by this hook. The earlier PDF diagnosis remains researcher-assisted evidence, not autonomous extraction success. Step 3 is a separately bounded OCR evaluation; Step 4 is offline navigation fallback testing. Discuss this checkpoint before proceeding.
