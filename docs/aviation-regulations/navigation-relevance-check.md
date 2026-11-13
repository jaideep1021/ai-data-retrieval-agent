# Navigation relevance checkpoint

12 November 2026. Offline only.

Diagnosis: the fallback treated every model-labelled official navigation candidate as worth a document slot. The latest SerpApi results included generic government notice indexes with domestic licence snippets. Official publication does not establish task relevance.

For US bilateral tasks, navigation-labelled candidates now require an observed title/snippet cue for air/aviation/bilateral agreements or Open Skies. Candidates failing this heuristic are logged as navigation_without_scope_cue and omitted even when model-selected as navigation. Instrument selections are not changed by this rule. No hard-coded publisher or answer URL is added. Other task types retain existing behavior.

Saved-selection replay removes all seven generic navigation candidates from SerpApi's second search. Brave's ordering remains unchanged. This does not establish that any alternative would succeed, nor does it change the original live outcomes. It can reduce irrelevant requests but may miss relevant pages whose titles/snippets lack these terms. The deferred-navigation synthetic fixture was updated to explicitly describe an air-services agreement directory. Future evaluation must measure lost relevant leads as well as avoided irrelevant requests.

Validation: 195 tests run, 194 passed, one optional browser test skipped. git diff --check passed. Replay evidence: runs/navigation-scope-replay-20261112/results.json. No network/Gemini calls, new events, live-trial claims or GitHub push.

Remaining issue: accessible substantive source routes are still unresolved. Do not repeat the unchanged broad trial simply to seek a positive result. A separately labelled source-access diagnostic and scope discussion remain appropriate next steps. The final regulatory CSV and full country/topic evaluation are incomplete.
