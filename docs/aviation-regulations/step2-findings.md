# Part 2: autonomous regulatory extraction demonstration

Completed 9 November 2026. Development only; no release or provider ranking.

## What changed

Added aviation_agent.py with explicit task/event schemas, shared Gemini-generated
queries, observed-link selection, existing search/document adapters, bounded
extraction, quote/date-format checks and preserved local evidence. Every function
has an explanatory docstring. See [code walkthrough](code-walkthrough.md).
No existing Python module or published version was changed.

## Actual live runs

One Kenya aviation-safety task was run through both providers. No reference answers,
source inventory or supplied document URLs entered the task. The first run failed
at extraction with HTTP 400 on both providers. The nested event JSON schema retained
additionalProperties, which the existing adapter removed only at the root. A local
schema override removes the unsupported wire keyword while preserving strict local
validation. The complete autonomous task was then rerun in a separate folder;
queries were regenerated, not taken from known documents. Both providers shared
the same queries within each run. Both runs are preserved locally.

| Corrected run | Search requests | Document attempts | Machine proposals | Mechanical audit |
| --- | ---: | ---: | ---: | --- |
| SerpApi | 1 | 3 | 1 | Needs human review |
| Brave | 1 | 3 | 1 | Unsupported quotation |

SerpApi retrieved parliamentary metadata for Kenya's 2018 Safety Management
Regulations. The proposed announcement date came from an issued-date metadata
field. That is not sufficient to verify an announcement date; it requires source
review and may need to be left unknown. Effective date remained null.

Brave retrieved a KCAA security-regulations PDF. The model combined source fragments
with an ellipsis rather than returning a contiguous quotation, so the grounding
check flagged it as unsupported. Security versus safety scope and the document's
legal status also need review. Both dates remained null. Only the leading 24,000
characters of the 262,777-character PDF were supplied, so absent dates in the
excerpt cannot establish that the full document lacks them.

These outcomes expose genuine next-step requirements: semantic date validation,
precise quotations, scope checks, competent-source assessment and document-section
selection. Neither proposal is a verified event. No accuracy percentage is justified
from this one-task development demonstration.

## Usage and checks

Across both runs: four search requests total (two SerpApi, two Brave) and eleven
Gemini HTTP attempts, including the two rejected extraction requests. No quota
response was observed. Seven-second model pacing was used. No billing changes or
purchases were made. Account invoice totals were not independently checked; this
report records actual request counts, not an invented dollar charge.

The final offline suite ran 127 tests: 126 passed and one optional browser test was
skipped. Ten tests cover the new module, including unknown dates, impossible dates,
unsupported evidence, strict input fields, schema compatibility, empty searches,
fetch failures, evidence persistence and invalid selection indices.

Raw runs: runs/aviation-demo-20261109 and
runs/aviation-demo-20261109-schema-fix (ignored, not publication artifacts).
Evidence hashes were checked against saved bytes. .env and both run directories
are ignored. Nothing was pushed. Next: discuss these findings before implementing
the authority/date/semantic verification deliverable and expanding to six tasks.
