# Optional OCR screening integration

12 November 2026. Offline checkpoint.

aviation_agent.py now accepts --ocr-screening. Default behavior is unchanged. For commercial tasks, a preserved parent PDF with PDF_HAS_NO_EXTRACTABLE_TEXT can trigger at most one local OCR attempt per provider run (two for the paired CLI run). Each attempt retains the standalone three-page/120-second limits. Attachments are not OCR-enabled by this change.

The document retains READ_FAILED and its native parser reason. OCR provenance and partial coverage are nested separately. Successful OCR produces a screening record: PROPOSED_EXCLUSION for an explicit counterpart mismatch, otherwise NEEDS_REVIEW. Both retain verified=false and OCR_REQUIRES_VISUAL_REVIEW; partial input also receives DOCUMENT_NOT_FULLY_EXAMINED. OCR text is not passed into event extraction or accepted CSV output. Thus this is screening integration, not full OCR-to-event automation. Missing tools remain UNAVAILABLE, and failures retain the underlying preserved PDF. No OCR result repairs or overwrites historical run evidence.

The CLI manifest records opt-in configuration and per-provider attempt cap and hashes the OCR module. Usage counts record actual OCR attempts. The existing search/model/document caps remain unchanged.

Validation: 194 tests run, 193 passed, one optional browser test skipped. Integration tests cover default-off behavior, one-attempt cap across two parent failures, unchanged READ_FAILED status, review flags and no event generation. Standalone missing-tool and timeout tests remain passing. git diff --check passed. No new network/model calls or push.

Next: separately labelled bounded live validation of navigation and optional screening. Remaining country/topic evaluation and verified-event dataset are not complete. Full automatic OCR-to-event extraction needs further provenance-aware verification work and should not be implied by this flag.
