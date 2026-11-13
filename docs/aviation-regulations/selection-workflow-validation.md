# Selection workflow validation

11 November 2026. Offline engineering checkpoint; not a new live retrieval experiment.

## Implementation

`aviation_selection.py` defines structured candidate roles and concise selection explanations. Commercial selection must assess every supplied index exactly once; duplicate, missing or out-of-range indices fail before fetching. Roles distinguish instruments, official navigation pages, secondary leads, unrelated results and uncertain results. Explanations are model judgements, not independently verified facts.

The runner saves the actual selection input, full structured output and dispositions: not selected, deferred, scheduled and attempted. This distinguishes model rejection from document-budget truncation. Previously selected but unvisited URLs are carried into the next selection even when the next search returns no results. They are reconsidered, not blindly fetched. Access history includes URLs, hosts, status and safe failure metadata. The prompt encourages another relevant observed publisher after repeated access failures; it does not blacklist a publisher or assert that other sources work.

Candidate input is capped at sixteen entries, with deferred leads first, then new results and observed links. Omitted counts are logged; this is a disclosed recall limitation to keep explanations bounded under the inherited response-token limit. A navigation page can lead to observed links; it is not itself verified regulatory evidence. Parent and attachment budgets remain unchanged. A third query or unlimited navigation is not introduced.

## Verification performed

179 tests run: 178 passed, one optional browser test skipped. Four new tests validate missing/duplicate assessments, out-of-range selection, saved non-selection reasons, and an integrated two-search sequence. In that sequence two inaccessible pages consume their slots, a third directory lead survives deferral, the second search is empty, and the directory is still attempted within the original three-document limit. The selector receives the two earlier failures. No event is invented from the directory.

Existing tests continue to cover wrong counterparts, date evidence, access errors, extraction, review and other project behavior. `git diff --check` passes. Test logs and revised configuration hashes are saved locally under `runs/selection-readiness-20261111/`.

## Research interpretation and limitations

This validates control flow and observability with synthetic fixtures. It does not establish that Gemini will select better sources, that the real agreement is accessible, or that the new live structured response will always fit its token budget. Alternate-publisher preference is advisory, not a guarantee. Generic retrieval failures still have only the existing safe reason where the underlying reader provides no finer code. Original live results are preserved and not reclassified as successes.

The new method changes selection schema, prompt, context and queue handling. A future trial must have a new run directory and configuration fingerprint. Any comparison is developmental and cannot isolate one change's causal effect. Do not supply researcher-found document URLs to the autonomous trial. All substantive proposals still require review.

## Next checkpoint

The implementation is offline-ready for one separately recorded bounded live trial after discussion. No search/model calls, purchases, human-label changes, accepted event CSV or GitHub push occurred in this checkpoint. Stop and diagnose if the live method still cannot access relevant evidence; do not keep rerunning until a favourable result appears.
