# Part 3: evidence selection and verification findings

Completed 9 November 2026. Development experiment; no verified CSV or release.

## Design

Replayed all three readable documents from the preserved Kenya demo: two
parliamentary metadata pages and one 96-page KCAA PDF. For each, compared the
leading-text policy with document-wide section ranking under the same new schema
and prompt. Both arms had a 24,000-character source-text budget. Page markers and
local overlap handling cause small input differences beyond selection alone.
Short pages fit completely in both conditions. Order alternated; one call was made
per condition/document. This is a diagnostic comparison, not statistically reliable
accuracy measurement. Researcher follow-up documents were not supplied to the model.

## Observations

| Document | Prefix condition with new schema | Document-wide condition with new schema |
| --- | --- | --- |
| 2018 Safety Management metadata | Classified as metadata; 2018-05-04 retained as issued date | Same interpretation; announcement/effective fields remain null |
| 2019 Unmanned Aircraft Systems metadata | Proposed a 2013-12-31 issued date from a generic Date field | Same proposed date; verifier flags unsupported date type in both arms |
| Security-regulations PDF | Called final/enacted based on opening provisions | Called draft after seeing incomplete 2020 dating line; verifier flags status and scope |

The PDF prefix covered pages 1–12. Section selection included pages
1, 2, 17, 18, 19, 26, 42, 43, 47, 91, 95 and 96. The final dating line was available
only to the latter condition. Both arms retained null full announcement/effective
dates. Neither arm proves enactment or draft status conclusively: that remains a
human-review question. The draft label is a model inference supported by a warning
sign, not an established legal conclusion.

The old Part 2 schema had mapped the metadata issued date into announcement_date;
the new schema separates it. This descriptive before/after comparison changes
schema and prompts together; it does not attribute improvement to one component.
The new evidence-list format yielded grounded separate passages on these cases,
including the PDF formerly rejected for a spliced quotation. Quote occurrence alone
still does not validate the descriptions or international applicability claims.

## Implementation and limitations

Added aviation_verification.py and replay_aviation.py; the autonomous CLI now uses
the same new extractor on documents it discovers. Existing PEP/DOT code is unchanged.
The narrow source-role registry distinguishes repositories from regulators, and
unknown hosts are flagged for classification. It is incomplete and does not attach
probabilities to authority. An official regulator can publish a draft.

Date checking validates explicit calendar wording and type cues; it is not a
complete semantic or legal verifier. A cue can be present in the wrong context.
Section ranking can omit decisive pages. In particular, the section-selected PDF
output's international-applicability evidence is weak and needs human examination.
The unexpected 2013 repository date for a 2019-titled document should be treated as
an unresolved discrepancy, not repaired from intuition. No candidate is automatically
accepted and no date is guessed or silently overwritten. Cross-source conflict
resolution, historical continuity and final reviewed CSV production remain future
work. All six country/topic searches have not yet been run.

## Validation and resource usage

Six Gemini calls succeeded; no retries, no search requests and no purchases/billing
changes. Seven-second pacing was used. Account invoice balances were not inspected.
The comparison consumed existing free-tier access; actual request usage is recorded
in the local manifest. Original evidence raw-byte hashes were verified before calls;
saved-text hashes and source-code hashes were recorded. Raw-byte matching is not
proof of completeness or correctness of PDF extraction.

Final offline suite: 140 tests run, 139 passed, one optional browser test skipped.
New checks cover section coverage/budgets, exact and spliced quotations, metadata
and conflicting dates, incomplete dating lines, host lookalikes, nested schemas
and the enhanced autonomous integration. No new live autonomous search was run in
Part 3: the comparison is explicitly a saved-document replay.

## Review and next decision

Read [verification guide](verification-guide.md) and [sanitized results](step3-results.json).
Local evidence and the detailed review sheet are under
runs/aviation-verification-20261109/; those are ignored and not publication files.
Discuss the observed improvements and unresolved issues before expanding to six
tasks. No percentage accuracy, provider superiority or generalization is claimed.
