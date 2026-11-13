# Step 3A: recovery test repair

11 November 2026. Offline only; no production changes, network or model calls.

Updated the staged-retrieval fake reader to accept preserve_raw keyword arguments. Added explicit assertions that all three attempted documents reach ACCESS_ERROR / SERVICE_ERROR_PAGE, preventing a TypeError from silently satisfying the recovery assertions.

Added a commercial-scope runner test using the real BusinessRetriever with mocked download and PDF parser. It asserts READ_FAILED / PDF_HAS_NO_EXTRACTABLE_TEXT, exact preserved bytes and hash, a second access-recovery search with the parser failure reason, bounded parent attempts, and no extraction stage or events. The second search is synthetic and returns no candidates.

Validation: five focused tests passed; full suite ran 185 tests, 184 passed and one optional browser test skipped. git diff --check passed. Earlier 184-test results were real but the old test did not establish the intended service-error path; these new assertions close that gap.

OCR implementation and counterpart-screening changes remain pending. No commit or push was performed. Next checkpoint: optional bounded local OCR evaluation on saved development PDFs with explicit page coverage and provenance.
