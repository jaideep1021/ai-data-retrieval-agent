# Commercial aviation access diagnostic

Date: 2026-11-11

## Method
Three previously observed official URLs were checked with the existing reader. This is an assistant-selected access diagnostic, not autonomous discovery or a provider comparison. No search API or Gemini calls were made. No verified events were produced.

## Results
- State Department agreement directory: robots.txt returned HTTP 403. The reader stopped under its existing policy before fetching the target page. This does not prove the agreement is unavailable.
- DOT Air Service Agreements: read successfully (3,108 characters). The saved HTML contains a relevant HTTPS link to the list of agreements being applied, but it is absent from the returned 40-link shortlist. Generic navigation and data-link prioritization can crowd out relevant content links. Older State Department links use HTTP and are excluded by the HTTPS-only reader. No linked pages were fetched. This general overview is not country-specific event evidence.
- ICAO agreement database: EMPTY_SOURCE. The attempt returned no usable text; the underlying cause and database accessibility remain unestablished.

## Changes and verification
The selection prompt now permits supported pre-period background and relevant official navigation leads without a country in their title. Known reader failures receive safe, specific diagnostic codes. Prompt behavior has not yet been revalidated with live Gemini.

Offline tests: 180 run, 179 passed, one optional browser test skipped. This is software validation, not retrieval accuracy.

## Next checkpoint
Improve content-link prioritization within existing limits using saved HTML tests before another bounded live trial. Preserve HTTPS and robots safeguards. Keep original machine outputs separate from diagnostics and human corrections. No historical applicability or commercial coverage claim is justified yet.

Local evidence: runs/commercial-access-diagnostic-20261111/results.json and document-2.bin / document-2.txt. Raw evidence remains private and ignored.

## Content-link fix: completed offline checkpoint

The shared reader now considers main/article content before site-wide navigation, then prefers document downloads within each content tier. Navigation remains a fallback. The candidate limit stays 500 and the returned shortlist stays 40. Literal HTTPS URLs, public-address checks and robots rules are preserved; HTTP links are not rewritten. Self-links and duplicate fragment variants are omitted. This change is domain-independent and does not inject country answers or source URLs.

Offline replay of the saved DOT HTML places the previously omitted agreements-being-applied link at position 2 of 40. Evidence: runs/commercial-access-diagnostic-20261111/link-shortlist-replay.json. No network or model calls occurred during replay. This is a development-page regression check, not an independent accuracy evaluation. Large-navigation and nested-navigation tests cover candidate-budget crowding, duplicate links, HTTPS filtering and download ordering.

Validation after the fix: 182 tests run, 181 passed, one optional browser test skipped. git diff --check passed. An initial new test caught a file-extension matching issue; it was fixed before this passing run.

Remaining limitations: HTML without semantic main/article markup may still mix content and navigation; the 40-link cap may omit useful links; a high-ranked navigation link is not verified event evidence. Live selection, access to linked documents and historical applicability remain untested for this revised method. Next: a bounded live checkpoint under recorded limits, reported separately from older trials. No GitHub publication occurred at this checkpoint.
