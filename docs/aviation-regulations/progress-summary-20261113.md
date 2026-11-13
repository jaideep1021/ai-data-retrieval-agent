# AI Web Agent: progress and next steps

Jaideep Manupati | Prepared 12 November 2026 for the 13 November meeting

## Progress to date

The project extends the original evidence-grounded Python agent rather than replacing it. Week 1 established PEP retrieval, Gemini extraction, source evidence and reference-based checks. Week 2 added autonomous query generation, SerpApi/Brave discovery, multi-source comparison, evaluation and a documented DOT sample. These stages distinguish finding a plausible value from obtaining sufficient evidence to accept it.

The DOT experiment used 30 observations: six development and 24 held-out cases, covering fares, daily passengers and distances. In the specialized structured workflow, Brave and Socrata each retrieved and correctly accepted 24/24 held-out values; SerpApi retrieved none under the tested configuration. Mean provider times were 8.98, 8.59 and 2.89 seconds respectively. Socrata is a public structured-data service, not a general search engine. The successful workflow used declared DOT schema knowledge and no Gemini calls. These are workflow-specific results, not universal accuracy or search-provider rankings. Earlier document/LLM failures remain part of the record. See [Week 3 report](../week3-report.md) for methodology, costs and limitations.

## Commercial aviation extension

The current research application targets Kenya, South Africa and Nigeria, focusing on commercial bilateral air-service agreements and restrictions affecting international connectivity, with historical evidence relevant to 2009–2019. Announcement, signature, proposed signing, publication and entry into force must remain distinct. Unknown dates are retained rather than inferred.

Implemented locally:
- Task-driven query generation and bounded provider trials with selection explanations and request accounting.
- Public-source retrieval with access safeguards, PDF attachments and source hashes.
- Parent-document bytes saved before parsing, including failures; retrieval failures and parsing failures distinguished.
- Evidence/date/scope checks and a local human-review workflow developed during the earlier Kenya pilot.
- Content-link prioritization, run-local navigation queuing and publisher-access downranking; generic navigation now needs an agreement/Open Skies cue for bilateral tasks.
- Optional local OCR screening, with engine provenance, reviewed-page coverage and strict limits. OCR is screening only: it does not automatically generate verified events.
- Narrow counterpart screening for wrapped agreement headings and explicit memorandum party clauses.

## Latest observed results

The latest paired US–South Africa development trial used two searches and three parent-document attempts per provider. It made seven Gemini calls in total, including shared planning, and extracted zero events. SerpApi reached generic notice indexes; Brave encountered State Department access failures and an ICAO page with no usable text. OCR was enabled but not triggered. This run tested parts of the workflow, not full country/topic coverage.

Separate researcher-assisted diagnostics established that two Parliament PDFs concerned South Africa–Namibia, not the US. One memorandum envisaged signing in 2025, rather than documenting an effective date. Local OCR of three agreement pages and the one-page memorandum recovered their parties but introduced text errors. These are development fixtures, not independent evaluation successes.

A separately inspected DOT current Open Skies list was accessible and listed Kenya and Nigeria. It provided no historical effective dates or country-specific instrument links. South Africa's absence from that list does not prove absence of a bilateral agreement. A 2026 list cannot establish applicability throughout 2009–2019.

The subsequent offline navigation refinement removes seven generic directory candidates from a saved SerpApi selection. This is a hypothetical replay, not evidence of improved live retrieval. No verified target events have been added from these trials.

## Challenges and incomplete work

Official publisher status alone does not establish historical applicability, correct counterpart or substantive evidence. Access failures, image-only documents, ambiguous dates, irrelevant search results and generic directories require different responses. OCR can help read a page but can also corrupt names and dates. The counterpart rules cover narrow English layouts and are not a universal authority or scope classifier.

Still incomplete: full country/topic evaluation, the verified regulatory-event CSV, independently evaluated end-to-end historical retrieval, and final aviation results. Automatic OCR-to-event extraction is not implemented. The accept/retrieve/abstain cost-aware policy remains a research formulation; calibrated confidence, learned stopping and downstream causal analysis are not completed capabilities.

Current offline validation: 195 tests run, 194 passed and one optional browser test skipped. These tests validate software behavior, not regulatory accuracy. Latest changes are local development work awaiting publication review.

## Demonstration and decisions for the meeting

Demonstrate one structured DOT retrieval with provenance, then a saved aviation trace showing search, selection, access/parsing failures and preserved evidence. Show OCR and counterpart screening as separate diagnostic stages. Retain saved outputs as backup and label them clearly.

Agree on: (1) US bilateral versus additional intra-African coverage; (2) acceptable historical evidence when primary archives are inaccessible; (3) treatment of unknown effective dates; and (4) a fixed evaluation set and request budget. Freeze the revised method before broader evaluation, retain original machine outputs, and report human-corrected dataset quality separately. The immediate objective is traceable regulatory data acquisition; downstream ML and causal work should follow a defensible data-quality assessment.
