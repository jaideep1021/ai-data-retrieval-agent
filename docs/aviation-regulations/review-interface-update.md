# Focused review interface and PDF completion

Completed 10 November 2026. Local development; nothing published.

## Open and submit

Use http://127.0.0.1:8765 while the local service is running. If it is stopped,
double-click Start Aviation Review.command in the project folder. Keep the launcher
terminal open while reviewing. The launcher uses this checkout's existing Python
environment and private run pack; it is a local convenience, not a portable release
installer. Only loopback is bound, not a public network interface.

Three tabs show only the current review candidates, with three targeted questions
per document. Each question contains the current interpretation, why it needs
attention, an evidence passage, where to check and an expandable example. Example
answers are guidance, not pre-approved labels. Correction fields appear only after
choosing Correct. There is no JSON download/import workflow in this new page.

Submit review saves to the existing file:
runs/aviation-shadow-policy-20261109/human-labels.csv

Reviewer name, coverage, overall outcome, per-field decisions, correction values,
references and supporting passages are saved. Structured field decisions are in
field_reviews_json; a readable summary is in correction/evidence_reference. Extra
columns record the reviewed PDF hash, overall decision and coverage. The old base
columns remain. Earlier rows are not migrated into new judgments automatically.
The original model outputs never change. Before replacing a reviewed row the server
makes a timestamped CSV backup; submission history is also retained locally. A row
saved as supported records a reviewer opinion, not automatic legal certification.
Date correctness is marked not_separately_scored instead of inferring an assessment
of all dates from a general decision.

The current questions are researcher-authored for these three development cases.
They are not a validated general question-generation model. The old rich HTML
viewer remains preserved but is superseded for active review.

## Attached PDFs: actual actions

The agent parsed the observed repository download links from the saved HTML,
excluding the license attachment. Access attempts timed out, including a bounded
retry. Policy/robots checks did not complete; no access control or robots rule was
bypassed. The first failed attempt and retry remain in separate run folders.

Two title-based Brave searches then discovered official KCAA alternatives:

- Legal_Notice_No_91.pdf: downloaded and parsed, 20 pages, 55,677 text characters.
- Draft_CiviAviation_Unmanned_Aircraft_Systems_Regulations_2019_Revised.pdf:
  downloaded and parsed, 39 pages, 134,261 text characters.

These are recorded as alternative official sources, not claimed identical copies
of the repository attachments. The current interface opens these exact downloaded
files. The security candidate retains its earlier 96-page PDF. No manual upload
was required.

Gemini analyzed selected sections of both new PDFs, not every page. Both extractions
succeeded. One bounded UAS repair attempt received HTTP 503 and produced no corrected
output; it was stopped at its request cap and is preserved. The interface therefore
flags the quotation/status issues from the original extraction instead of presenting
them as repaired.

The safety-management PDF supplies a Gazette publication date and a separate dated
line, plus a revocation clause. The generated description muddles the revoked year;
the focused review card asks for an evidence-backed correction. UAS final status
and quotation support remain uncertain. The filename's Draft marker is now flagged
as a status warning, not taken as conclusive legal proof.

## Code and limits

aviation_attachments.py discovers only observed PDF links and downloads with public
HTTPS/robots safeguards. Attachment callers opt into 20 MB and a 60-second read
 timeout; old BusinessRetriever/pdf_text callers retain 10 MB/default timeout.
Existing PDF process-time, page-count and extraction limits remain.

The enhanced autonomous workflow follows observed PDF attachments before extracting
metadata and may spend its remaining search slot on a title-based official-copy
fallback. It permits at most two attachment attempts per trial in addition to three
candidate-document attempts, while retaining the two-search cap. Alternative
version uncertainty and failures are logged. This integrated path has offline tests;
the live follow-up used the same helpers on saved discovery evidence, not a fresh
six-task autonomous benchmark.

aviation_review_server.py provides the local UI and validates submissions. It rejects
unknown/stale source hashes, incomplete corrections, missing reviewer information,
cross-origin writes and unexpected Host headers. Only packaged PDF paths are served.
CSV replacement is atomic and spreadsheet formula prefixes are escaped. This is a
single local reviewer workflow, not a production multi-user review service.

## Validation and usage

- Offline suite: 154 tests run, 153 passed, one optional browser test skipped.
- Browser: three focused tabs; Submit wrote to an isolated CSV copy; reloading
  restored decisions/notes; incomplete corrections rejected; all three saved PDF
  links worked; narrow layout checked; unauthorized-origin POST rejected.
- User's actual labels file was byte-for-byte unchanged by browser tests.
- Two Brave search requests, zero SerpApi requests; three Gemini attempts total
  (two successful extractions, one HTTP 503). No purchases or billing changes.
- Private runs, human labels and .env remain ignored. No GitHub push.

The interface is ready for review, but the events are not certified. Unknown dates,
legal-status ambiguity and scope decisions remain visible for the reviewer.
