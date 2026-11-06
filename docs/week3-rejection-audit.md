# Week 3 audit: why correct Week 2 candidates were not accepted

## Scope and answer

Offline audit of all 40 autonomous trials in the completed paced Week 2 run.
No new API calls, rescoring, source downloads or pipeline changes were performed.
Correctness retains the original frozen-reference scoring definition.

There were 19 correct candidates: 18 Brave and one SerpApi. Six were accepted.
Of the **13 correct candidates not accepted**, **12 had only one usable grounded
source** and **one had a title-prefix conflict**. Brave contributed 12 of the
13 cases; SerpApi contributed one. This is a diagnostic conditional count, not
13 failures out of 20 or an independent estimate of factual error.

The comparison policy required at least two grounded sources with matching
normalized strings and different evidence hashes. It did not allow an official
publisher's single record to establish acceptance. The correct single-source
candidates came from official PEP pages or the python/peps repository. The code
therefore abstained as designed even though the offline answer key matched.
A source being correct in hindsight does not mean that accepting it was justified
without an explicit authority and context policy at decision time.

## Case-by-case findings

| Observation | PEP / field | Provider | Decision | Explanation |
|---|---|---|---|---|
| obs-02 | 776 / status | brave | INSUFFICIENT_EVIDENCE | A second page returned no supported claim. |
| obs-03 | 3156 / type | serpapi | INSUFFICIENT_EVIDENCE | Only one source was recorded and grounded; no second usable claim was available. |
| obs-04 | 804 / created | brave | INSUFFICIENT_EVIDENCE | Only one source was recorded and grounded; no second usable claim was available. |
| obs-06 | 799 / status | brave | INSUFFICIENT_EVIDENCE | Only one source was recorded and grounded; no second usable claim was available. |
| obs-09 | 233 / title | brave | INSUFFICIENT_EVIDENCE | A second URL redirected to the same source and was deduplicated. |
| obs-10 | 714 / status | brave | INSUFFICIENT_EVIDENCE | Only one source was recorded and grounded; no second usable claim was available. |
| obs-11 | 758 / type | brave | INSUFFICIENT_EVIDENCE | Second claim quoted the type as its entity evidence; it did not identify PEP 758. |
| obs-12 | 342 / created | brave | INSUFFICIENT_EVIDENCE | Second claim used an issue-opening date with unsupported quote/value matching; a third attempt recorded ValueError. |
| obs-13 | 467 / title | brave | CONFLICT | Two grounded title strings differed only by the PEP 467: prefix; another URL was a duplicate. |
| obs-15 | 671 / type | brave | INSUFFICIENT_EVIDENCE | Second source attempt recorded ValueError; the artifact does not preserve its detailed message. |
| obs-16 | 436 / created | brave | INSUFFICIENT_EVIDENCE | Only one source was recorded and grounded; no second usable claim was available. |
| obs-18 | 419 / status | brave | INSUFFICIENT_EVIDENCE | Only one source was recorded and grounded; no second usable claim was available. |
| obs-19 | 805 / type | brave | INSUFFICIENT_EVIDENCE | Only one source was recorded and grounded; no second usable claim was available. |

These explanations distinguish the immediate decision rule from deeper causes.
For single-source cases, the saved outcome proves a corroboration shortfall; it
does not prove that no corroborating source exists anywhere on the web. Source
selection, query limits and extraction coverage can all affect that shortfall.
The ValueError artifacts retain only the exception type, so a more specific cause
cannot be reconstructed reliably from those records.

## Other failures must remain separate

- Nineteen SerpApi trials had no grounded candidate: eight ended in an error and
  eleven in insufficient evidence. These are not correct values rejected by verification.
- Brave's PEP 841 and PEP 818 first candidates included PEP title prefixes and
  failed the original strict scoring. They are not counted among the 13 above.
- PEP 818 also contained a different discussion heading. Removing a prefix alone
  would not resolve all its source differences; document/version context needs review.
- PEP 467 is a clear formatting conflict in the saved strings. A carefully scoped
  title-normalization rule is a proposed improvement, not an applied score change.
- Duplicate evidence was not the final decision for any of the 13 cases. A duplicate
  URL contributed to a corroboration shortfall in PEP 233; duplicate DOT rows are
  a separate Week 3 finding. These mechanisms should not be conflated.

## What this implies for verification

1. Classify source provenance and match entity, attribute and time before deciding
   whether additional corroboration is needed. One original publisher may be more
   relevant than multiple derivative pages.
2. Separate normalization differences from substantive conflicts. Preserve raw
   values and explain any transformations; do not relax rules simply to match answers.
3. Explain abstention with a specific reason: no candidate, unsupported quote,
   one usable source, duplicate evidence, context mismatch, or substantive conflict.
4. Keep authority, groundedness, agreement and reference correctness as separate
   concepts. None alone is a universal guarantee of truth.

The DOT adapter implements a limited publisher/context acceptance policy and
compares it against agreement on the same evidence. It has not been applied to
these PEP trials, and no improved PEP acceptance rate is claimed. A transferable
policy still needs implementation and evaluation on new cases, including errors
from authoritative sources and conflicting evidence.

## Reproduce and inspect

Run `python scripts/audit_week2_rejections.py` from the repository root. It needs
the private original run folder `runs/evaluation-deliverable3-paced-20261028`.
A public clone can inspect [sanitized audit records](week3-rejection-audit.json)
but cannot rerun the evidence audit without those private artifacts.
The audit verified all 35 captured autonomous evidence files against saved hashes,
checked decisions against the published results, and recorded original result hashes.
Raw pages, snippets and personal contact details are excluded from the audit output.
The original [Week 2 results](evaluation-results.json) remain unchanged.
