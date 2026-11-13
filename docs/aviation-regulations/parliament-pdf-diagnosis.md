# Parliament PDF diagnosis: first checkpoint

11 November 2026 (America/New_York).

## Method
Researcher-assisted diagnosis of two URLs already discovered by SerpApi; separate from autonomous evaluation. Two PDF downloads through the existing bounded reader and robots policy (robots returned 404), no search or Gemini API calls. Preserved exact bytes and SHA-256 before parsing. Rendered the first three pages of document 1 and the sole page of document 2 with Poppler, bounded to 1,600 pixels on the longest side and a 60-second process timeout. Inspected all four images visually. No OCR dependency installed and no OCR run.

## Findings
- Document 1: HTTP 200, 1,326,138 bytes, 29 pages. Cover and preamble identify South Africa–Namibia. Page 3 defines scheduled international passenger, baggage, cargo and mail services. Commercial subject matter is relevant in general, but the counterpart is wrong for the US bilateral task. Exclude this candidate from that task.
- Document 2: HTTP 200, 53,342 bytes, one page. Memorandum explicitly identifies South Africa–Namibia. It seeks authorization to sign and anticipates signing at an ICAO assembly scheduled 23 September–3 October 2025. That is a planned signing window, not a verified signing or effective date, and does not establish a 2009–2019 event. Exclude this candidate from the US bilateral task.

Both render legible printed text but pypdf returns zero text on every inspected page. This supports a need for OCR for automated reading of those pages; it does not establish all-page internal PDF structure. The agreement's remaining 26 pages were not visually reviewed. Its final execution and effective date were not determined. No dates were inferred from file metadata.

## Research implication
The failure was not solely missing OCR: document relevance was also unconfirmed at selection time. OCR would help classify and reject these leads, not recover a US–South Africa event from them. Neither document warrants further Gemini extraction for the current task. Do not reinterpret these as verified historical intra-African events without a separately approved scope and date review.

## Evidence and remaining work
Raw files, page images, manifest, diagnostic script and visual-review.json are private under runs/parliament-pdf-diagnosis-20261111/. SHA-256 values were rechecked against saved bytes. Original trial outputs and human labels remain unchanged. No production code changes, broad trial or GitHub push occurred.

Next checkpoint: fix parent-document preservation before parsing and test the extraction-failure path. OCR and navigation-fallback implementation remain pending. This diagnostic is not a completed automated preservation feature.
