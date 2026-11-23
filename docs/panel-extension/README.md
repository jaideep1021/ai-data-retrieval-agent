# Africa aviation and trade extension

## Current package

The latest private workbook is `runs/clarified-panel-20261123/outputs/review/Africa-clarified-extension.xlsx`. It contains 364 rows and 76 columns for 2020 Q1-2026 Q2, with scheduled services primary and all-service comparisons retained. Missing values remain blank. The supplied reference is unchanged; no full historical merge is claimed.

Read the [clarified update](clarified-update-20261123.md) for coverage and reproduction, and [applied decisions and limitations](final-review-decisions.md). The [v0.5.0 findings](release-v0.5.0.md) describe the earlier published snapshot; these local changes do not move that tag.

The new offline build is `python apply_panel_decisions.py --out runs/clarified-rebuild`. Collection is in `collect_panel_additions.py`; presentation is in `scripts/build_clarified_panel_workbook.mjs`. The short PDF is beside the latest workbook. Earlier workbooks remain preserved.

## Offline checks

From the project root:

```sh
python -m pip install -r requirements-panel.txt
python scripts/verify_panel_handoff.py
```

For the earlier v0.5.0 snapshot, the checker verifies 199 registered source hashes, rebuilds consolidation in a temporary directory, compares the CSV/JSON outputs exactly, checks unique country-quarter keys and verifies Excel cells against the saved data. It makes no API calls and does not overwrite the workbook. It requires the private runs/ inputs, which are intentionally not published.

This verifies consolidation from preserved processed inputs, not a fresh end-to-end replay of every raw-source parser. Earlier baseline revisions are required dependencies and must be retained. The Excel renderer is `scripts/build_consolidated_panel_workbook.mjs`; it additionally requires the artifact-tool JavaScript runtime, which is not installed by requirements-panel.txt.

## Processing and handoff

- BTS: `bts_bulk_download.py`, `build_bts_panel_package.py`, `compare_bts_reference.py`; saved all-geography annual downloads are in runs/bts-bulk/.
- Trade: `census_trade_panel.py`; monthly general imports and total exports become separate quarterly sums in USD millions. Annual totals remain in the trade package. Historical date discrepancies remain documented.
- Economics: `worldbank_panel.py`, `validate_worldbank_panel.py`.
- Fuel: `fuel_source_check.py`; US fuel accepted; BTS quarter-end and EIA mean spot measures remain distinct.
- Tourism: `process_un_tourism.py`, `process_tourism_ratios.py`.
- Immigration: `collect_immigration_candidates.py`; ACS birthplace counts match the clarified immigration concept; unavailable values remain blank.
- Derived aviation: `derive_aviation_candidates.py`, `classify_aviation_markets.py`.
- Income: `income_group_candidates.py`; preserved dated alternative; the clarified main panel now holds the reference labels fixed.
- Final consolidation: the preserved consolidation-reproduction.py in revision 3; source-register.json links all input hashes.

Consult each script's help and corresponding checkpoint before new collection. Annual values repeat within the same year without interpolation or carry-forward. Missing source observations are not automatically zero. Remaining candidate names preserve unresolved historical definitions.

## Reuse for South America

1. Confirm country list and definitions; use a separate region configuration and output folder.
2. Reuse the all-geography BTS annual files, filtering countries locally rather than downloading by country.
3. Map BTS, Census and World Bank codes independently. Do not transfer Africa-specific tourism categories or reference-derived conventions.
4. Include both US travel directions, explicit service filters and the requested cutoff. Distinct airlines and source-record counts are separate measures.
5. Collect new region-specific series only when existing snapshots do not cover them; preserve URLs, dates, units, transformations and hashes.
6. Validate keys, quarterly completeness and missing versus zero. Compare to reference data if available; document unresolved definitions before finalization.

## Privacy and status

Raw data, reference snapshots, review workbooks and correspondence stay private. No publication is authorized by this checkpoint. Collection is researcher-configured; it is not evidence of fully autonomous discovery. The current report distinguishes applied decisions from remaining access and historical-comparability gaps.
