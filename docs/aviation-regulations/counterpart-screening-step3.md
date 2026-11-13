# Step 3C: counterpart screening

12 November 2026. Offline implementation and development replay only.

The two-government heading rule now tolerates whitespace and line wrapping inside government/republic prefixes, including THE followed by a newline before REPUBLIC. A separate narrow memorandum rule requires an Explanatory Memorandum heading and the explicit clause that two governments have reached consensus on the draft text of the Agreement. Both preserve literal evidence spans and label the matching basis. Conflicting detected pairs and unmatched layouts return None: unresolved, not accepted.

Replay of the two saved OCR outputs identifies South Africa–Namibia in both the cover and memorandum. Both are EXPLICIT_COUNTERPART_MISMATCH for the US task. Input hashes and evidence spans are stored in runs/counterpart-screening-20261112/results.json. This uses known development examples and does not establish independent accuracy. The OCR tool remains standalone; this replay does not demonstrate automatic live OCR integration.

Tests cover wrapped prefixes, memorandum prose, US counterpart, negation of the consensus clause, missing memorandum heading, conflicting detected pairs, incidental country mentions and unrelated task scope. Full suite: 189 tests run, 188 passed, one optional browser test skipped. git diff --check passed.

Limits: narrow English-language patterns, bounded leading text, no comprehensive country-name validation or semantic entailment. OCR can corrupt country names. An embedded quotation or unusual comparison can still mislead a pattern-based detector. No claim of universal counterpart recognition, date verification or historical applicability. Unknown layouts remain reviewable. No search/Gemini calls, additional PDF downloads, commits or pushes.

Next checkpoint: offline navigation fallback rules using saved candidates and selection outputs, not new model selections. Review Steps 2–4 together before another live trial.
