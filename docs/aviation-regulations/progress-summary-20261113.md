# Commercial Aviation Agent Progress Report

Research update | 13 November 2026 | v0.4.0

## Purpose and outcome

We extended the existing AI Web Agent to investigate historical commercial aviation agreements and policy information for Kenya, South Africa and Nigeria, with relevance to 2009–2019. The work established a traceable retrieval and review workflow and identified concrete document-access and interpretation problems. It has not yet produced a verified US–Africa agreement dataset.

## Foundation from earlier work

The original prototype retrieved PEP metadata and preserved supporting evidence. Later work added autonomous queries, SerpApi and Brave search, and multiple-source comparison. The DOT experiment used 30 observations: six development cases and 24 held-out cases. In the specialized structured workflow, Brave and Socrata each recovered and correctly accepted 24 of 24 held-out values; SerpApi recovered none in that earlier configuration. These results describe that experiment, not a universal ranking of services. The successful structured route used DOT schema knowledge without Gemini.

## Commercial aviation implementation

Following the clarification that the focus was commercial aviation, we adapted the agent to identify agreement parties, commercial provisions, document status and distinct date types. Gemini generates search queries and proposes structured claims from retrieved passages. SerpApi and Brave discover possible sources. The program limits requests, preserves downloaded evidence and records failures. A local interactive architecture guide explains the workflow and lets users inspect saved results.

## Observed findings

The bilateral-agreement development trials focused on US–South Africa. An early Brave trial proposed a South Africa–Chad agreement and a precise signing date not explicitly supported by its garbled quotation. The checks flagged the party evidence and date; the candidate remained unverified. Later paired trials, including the 13 November demonstration, extracted no events. Observed obstacles included irrelevant or generic pages, State Department access failures and an ICAO response without usable text. No extraction does not establish that no agreement exists.

## Document reading and OCR

Two separately examined Parliament PDFs concerned South Africa–Namibia, not the US counterpart. One memorandum described a proposed 2025 signing window, not a verified effective date. Ordinary PDF text extraction failed, although the pages were visually readable. Bounded local OCR recovered text with some errors; the longer document was examined through three of 29 pages. Coverage and source hashes were recorded. OCR currently supports screening, not automatic creation of verified events.

## Verification and human validation

Automatic checks test whether quotations occur in the cited passages, whether the country and party evidence match the task, and whether proposed dates are explicitly supported by their wording. They flag drafts, metadata-only records, uncertain source roles and unresolved historical applicability. Signature, publication and entry into force remain separate. These checks are conservative rules, not a complete legal interpretation or calibrated confidence measure. Every commercial candidate still requires human validation. Reviewers inspect context and record acceptance, correction, exclusion or an unresolved decision; original machine proposals remain separate from corrections.

## Coverage and interpretation

Kenya’s earlier pilot concerned safety and security documents; it is not a completed US–Kenya bilateral evaluation. Comparable US–Kenya and US–Nigeria agreement trials are not established in the inspected run records. A separately inspected current DOT Open Skies list mentioned Kenya and Nigeria but did not establish historical effective dates. The verified event CSV, full country-topic evaluation and independent regulatory-accuracy assessment remain incomplete. This report closes the current work period; further scope will follow the next assignment.

## Software validation and release

The recorded offline checkpoint ran 195 tests: 194 passed and one optional browser test was skipped. The v0.4.0 release commit passed Linux, macOS and Windows CI. Separate browser checks covered the interactive guide and saved-result loading. These checks establish software behavior, not historical or regulatory accuracy. A 13 November DOT demonstration also showed SerpApi accepting one fare record while another passenger query remained unresolved; these are additional observations, not a replacement benchmark. Public code and research documentation are available in the repository. Credentials, raw run evidence and private correspondence are excluded.

Repository: https://github.com/jaideep1021/ai-data-retrieval-agent

Release: https://github.com/jaideep1021/ai-data-retrieval-agent/releases/tag/v0.4.0
