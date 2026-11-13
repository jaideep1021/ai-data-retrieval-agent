# Step 3B: optional local OCR evaluation

11 November 2026. Standalone development tool; not wired into live retrieval.

## Setup and use
Installed free Tesseract 5.5.3 with English language data through Homebrew. Poppler was already available in the bundled runtime. No Python requirements changed. A separate machine needs tesseract, pdftoppm and pdfinfo on PATH. Missing tools produce UNAVAILABLE with a manifest; existing pipeline READ_FAILED records are not modified.

Run from the project root with the project Python:

```sh
python optional_pdf_ocr.py --source runs/parliament-pdf-diagnosis-20261111/parliament-1.pdf --output runs/ocr-new-document-1
```

Output must be a new runs/ directory. The API defaults to the first three pages, caps PDFs at 10 MB and 100 pages, rendering at 2,000 pixels on the longest side, each subprocess at 30 seconds and the run deadline at 120 seconds, with a 100,000-character assembled text limit. This is bounded processing, not a hostile-document security sandbox. The source is not modified. Page images, individual OCR text, combined text and manifest are retained.

## Actual findings
- Agreement: OCR_EXTRACTED; pages 1–3 of 29; partial_coverage true. Cover correctly recovers South Africa and Namibia with the observed line breaks. Preamble contains recognition errors such as South Aftica.
- Memorandum: OCR_EXTRACTED; page 1 of 1; partial_coverage false. Recovers Namibia and the proposed 2025 signing window, but also misrecognizes ICAO as JCAO near the end.

These are the same development documents visually inspected in Step 1. Both remain wrong-counterpart leads for the US task. No event extraction, effective-date validation or independent OCR accuracy estimate was performed. OCR_EXTRACTED is a processing status, not verification. Every output requires visual review and dates_verified remains false. Full page coverage does not imply full semantic verification.

Local evidence: runs/optional-ocr-20261111/document-1/ and document-2/. The initial manifests include the known original parser reason for these two fixtures. The reusable tool uses explicit_local_evaluation as its trigger rather than assuming all future input PDFs had the same prior parser error.

## Tests and scope
188 tests run: 187 passed, one optional browser test skipped. New tests cover missing tooling, timeout recording and invalid page budgets. Two actual local OCR executions succeeded; original SHA-256 values match Step 1. No search or Gemini calls or new source downloads. Homebrew installation did require package downloads. No GitHub push.

Counterpart newline/prose screening remains the next checkpoint; navigation fallback remains Step 4. Automatic OCR integration into the live agent is not implemented. This explicit tool supplies the evidence needed to decide that integration, without changing earlier trial results.
