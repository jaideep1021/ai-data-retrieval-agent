# Commercial aviation: revised-selection live checkpoint

11 November 2026 (America/New_York).

## Design
One South Africa–US bilateral air-services development task, shared autonomous query generation, SerpApi and Brave. No supplied source URLs or correct answers. Existing limits: two searches, three parent document attempts, two attachments and six model attempts per provider; at most fourteen model attempts including shared planning. Seven-second model pacing. Prior runs remain unchanged.

## Observed results

| Measure | SerpApi | Brave |
|---|---:|---:|
| Searches | 2 | 2 |
| Parent attempts | 3 | 3 |
| Attachment attempts | 0 | 0 |
| Provider model attempts | 2 | 2 |
| Provider seconds | 19.493 | 9.942 |
| Extracted candidates | 0 | 0 |
| Verified target events | 0 | 0 |

Five successful Gemini attempts including shared planning; 5607 input tokens and 1639 output tokens. No extraction calls. Provider timings exclude shared planning and are affected by pacing and sequential order. No purchase or billing change was made; actual cash charges were not independently verified.

## Failure diagnosis
SerpApi attempted the known State archive agreement, which returned a service-error page. It then selected two South African Parliament PDFs; both failed with PDF_HAS_NO_EXTRACTABLE_TEXT. This suggests a need to inspect their rendering and evaluate OCR, but does not prove they are scanned or relevant US agreements. Neither PDF yielded candidate evidence.

Brave attempted the State archive agreement and archive directory, both service-error pages, and the current State list, blocked by the reader's robots policy. No policy bypass was attempted.

The model recognized prior-background agreements and official navigation roles in this run. Source roles remained imperfect (one archive agreement was labelled secondary). Recognizing a directory did not ensure selecting it. Neither provider fetched the DOT overview, so the revised content-link shortlist was not exercised live. Its saved-HTML regression result remains separate.

## Interpretation and next checkpoint
No extraction accuracy or provider superiority claim is justified. Queries and method differ from earlier runs, so this is a development sequence, not a controlled causal comparison. Do not infer historical applicability from search titles. The code hashes match the run manifest.

Before another broad trial, diagnose the two already-discovered PDFs with bounded download/render checks, preserve their bytes even if text extraction fails, and evaluate an explicitly labelled OCR fallback if needed. Review page evidence for counterpart and commercial scope before spending extraction calls. Also evaluate navigation-selection behavior offline rather than repeatedly searching unchanged inaccessible hosts. These are proposed next steps, not completed capabilities.

Local evidence: runs/commercial-zaf-20261111-content-links/. No human labels, verified-event CSV, additional country trials or GitHub push were produced at this checkpoint. Prior offline validation: 182 tests run, 181 passed, one optional browser test skipped.
