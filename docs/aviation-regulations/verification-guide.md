# Part 3: regulatory verification guide

This development extension improves evidence selection and review. It does not
certify laws or publish a verified CSV. Every candidate still requires human review.

## How the code fits together

The existing autonomous discovery remains in aviation_agent.py. Its command-line
runner now calls run(..., enhanced=True), which sends each discovered document to
aviation_verification.extract_review. The default Python function parameter remains
False to preserve the Part 2 comparator for old callers/tests. The code version and
hash manifest distinguish the new CLI behavior. No old run is overwritten.

| Function/schema | Purpose |
| --- | --- |
| split_sections | Walk all saved text, preserve PDF page numbers and character offsets, and form overlapping passages. No OCR is added. |
| select_sections | Reserve opening/closing passages and rank the rest for dates, status and relevance within a 24,000-character excerpt budget. Prefix mode provides the comparison condition. |
| Evidence | Keep each exact quote tied to a section ID; two real passages are two objects, not an invented combined quotation. |
| DateObservation | Separate issued, published, announced, signed, effective, provisional-application and consultation dates. Partial dates retain wording with null normalized values. |
| RegulatoryEvent | Record topic, document status, applicability and supporting passages. All are model proposals until reviewed. |
| source_role | Identify narrowly registered hosts and publisher roles. An unclassified host is not necessarily unreliable; it needs review. No numeric confidence is invented. |
| date_in_wording | Check explicit full calendar wording against a proposed ISO date. Unsupported formats and ambiguous numeric dates require review. |
| assess | Check quote provenance, date wording/type cues, draft/metadata status, topic, applicability and conflicting dates. Return flags and provisional export dates, never verified=True. |
| extract_review | Run selection, Gemini extraction and deterministic checks through one shared entry point. |
| replay_aviation.execute | Reuse saved autonomously discovered documents, verify raw-byte hashes, compare selection modes, and record model usage without search calls. |

## What the selection does and does not guarantee

All extracted text is scanned locally. Gemini receives selected passages, not the
whole document. Page coverage and omitted sections are recorded in each result.
The ranking is a heuristic: a decisive provision can still be missed or split.
Opening/closing passage retention helps expose incomplete signatures and title/date
inconsistencies, but does not establish legal status. The exact quote check tolerates
whitespace/case normalization only; it does not treat a paraphrase as a quotation.

## Reproduce the saved-document comparison

With the existing environment/dependencies and local .env, from the project root:

```sh
python replay_aviation.py --source runs/aviation-demo-20261109-schema-fix --output runs/aviation-verification-new
```

The source run is private local evidence, not included on GitHub. Someone without
it must first perform their own autonomous demo; that is a new development dataset,
not an exact reproduction of these source documents. Raw PDF hashes, text hashes,
model name, seven-second pacing, source-code hashes and usage are recorded.

Up to three saved documents are evaluated with two selection modes. At most twelve
Gemini HTTP attempts including retries; zero search calls. The same new schema and
checks are used in both arms. Short documents may have identical inputs in both
arms, so differences there reflect model variability rather than selection gains.
This is not an accuracy benchmark or a provider comparison. Original Part 2 results
are a descriptive baseline with a different prompt/schema, not a controlled ablation.

## Human review steps

For each row in the local review sheet:

1. Open the source URL and saved text; locate the referenced PDF page/section.
2. Check that the quote supports the description, not just that it exists.
3. Establish whether the document is final, a draft, a consultation or metadata.
4. Identify the meaning of every date. Do not substitute issue/publication for
   announcement/effect. Incomplete dating lines cannot establish a full date.
5. Check country, time window, safety/security distinction and international scope.
6. Record supported / correction needed / unresolved / out of scope, with reasons.
   Do not mark all model candidates accepted simply because their host is official.

The date checks use lexical cues, not a learned or validated semantic verifier.
Historical continuity, default statutory commencement rules, treaty conditions,
independence between sources and completeness of the historical record require
additional evidence/review. No causal impact on connectivity is inferred.
