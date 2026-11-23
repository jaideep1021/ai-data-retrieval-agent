# Africa aviation and trade extension: clarified update

Release v0.5.1 | 23 November 2026 | 14 countries, 2020 Q1-2026 Q2

The revised extension contains 364 country-quarter observations and 76 columns. Scheduled aviation measures are primary, with corresponding all-service comparisons. The supplied 2015-2019 reference and preserved raw inputs are unchanged. This is an extension package, not a reconstructed 2009-2026 historical dataset.

## Decisions implemented

- Scheduled class F is primary; all-service F/G/L/P values remain separate. Distinct airline counts and source-record counts are retained.
- Carrier measures are labelled Foreign and US. Foreign includes all non-US carriers, not just African carriers.
- US fuel is retained: BTS quarter-end price and EIA mean monthly spot price, both USD/gallon. They are different concepts and are not combined. The empty African fuel-cost placeholder is removed.
- Immigration is the ACS estimate of US residents born in each named country, in persons, with margins of error. Fixed income groups use the constant labels in the supplied reference.
- Destination national unemployment and US quarterly unemployment are added. Positive observed scheduled departures support Nonstop=1; no returned activity does not establish zero.
- The existing GDP PPP conversion factor is retained, with a separate household/NPISH consumption PPP factor. Historical GDP/PPP replication remains qualified.

## Coverage

Counts are populated country-quarter cells, not independent annual observations or accuracy rates. Annual values repeat within year without interpolation.

| Measure | Populated / 364 | Qualification |
| --- | --- | --- |
| Census imports, exports and total trade | 364 each | USD millions; actual Census dates |
| Scheduled seats and passengers | 203 each | Three-month presence screen; not proof of complete reporting |
| All-service seats and passengers | 209 each | Separate comparison, not a fill for scheduled gaps |
| GDP, population and GDP PPP factor | 336 each | Annual 2020-2025 values; 2026 missing |
| US fuel, each measure | 364 | Same US series across destinations |
| ACS birthplace population | 232 | 58 source country-years |
| Fixed income groups | 364 | Reference labels held constant |
| Consumption PPP factor | 320 | 80 source country-years |
| Destination national unemployment | 180 | 45 source country-years; no modeled fill |
| US unemployment | 350 | 25 complete quarters across 14 countries |
| Nonstop scheduled observed | 215 | Positive evidence only; 149 unknown |
| Tourism arrivals | 180 | Country-specific source categories retained |
| Tourism receipts/expenditure ratios | 44 each | Limited published coverage |
| Compatible connectivity index | 0 | Missing |

## Verification and limitations

The build verified 199 registered baseline source hashes and five new response hashes. Retained values match the earlier panel exactly. All 304 release tests passed, including the local browser test. Fifty targeted panel tests passed, covering duplicate keys, incorrect series, incomplete quarters, missingness and zero handling. The exported workbook was checked against the prepared data across 81,150 cells. No new search-provider or Gemini calls were required.

BLS reports October 2025 unavailable due to the lapse in appropriations. Q4 2025 US unemployment is therefore blank; two-month averaging is not used. National unemployment definitions may differ across countries, and annual estimates are not quarterly observations. The separately downloaded ILO modeled series does not fill national gaps. Employment counts are not inferred from unemployment rates.

Unavailable tourism, immigration, connectivity and economic observations remain missing. Historical trade-date discrepancies and source-vintage differences remain documented. Published source estimates may themselves use estimation; the project performs no missing-value imputation. This researcher-configured collection does not establish causal effects, universal agent accuracy or complete source reporting.

## PPP and next use

GDP PPP factor (`PA.NUS.PPP`) and household/NPISH consumption PPP (`PA.NUS.PRVT.PP`) are different conversion factors, both in local currency per international dollar. They are not GDP amounts or market exchange rates. Both remain labelled separately rather than silently selecting a historical definition.

Preserve this unimputed version before later modeling or missing-data experiments. The collected package is ready for review under the clarified choices. Remaining issues concern historical reconciliation or unavailable data. For South America, reuse the bulk BTS files and processing approach with a separate country configuration.

## Reproduction

The offline build requires the preserved private inputs. From the project root:

```sh
python -m pip install -r requirements-panel.txt
python apply_panel_decisions.py --out runs/clarified-rebuild
python -m unittest discover -s tests -p 'test_*panel*.py' -v
```

`collect_panel_additions.py --out runs/new-source-snapshot` makes five bounded public requests, preserving URLs, UTC dates and hashes. To use a new snapshot, pass `--sources runs/new-source-snapshot` to the build. Fresh downloads may include revisions. Existing output folders are never overwritten.

`scripts/build_clarified_panel_workbook.mjs` renders workbook-data.json using the artifact-tool runtime. The exported CSV is usable without that runtime. Raw downloads, the reference and run folders stay private.

Sources: [BTS](https://www.transtats.bts.gov/), [Census trade](https://www.census.gov/foreign-trade/), [ACS B05006](https://api.census.gov/data/2024/acs/acs1/groups/B05006.html), [World Bank national unemployment](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/SL.UEM.TOTL.NE.ZS), [consumption PPP](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/PA.NUS.PRVT.PP), [BLS series](https://api.bls.gov/publicAPI/v2/timeseries/data/LNS14000000), [EIA](https://www.eia.gov/). Exact download URLs and times remain in the preserved manifests.

## Reading the aviation flags

`NO_SELECTED_RECORDS` means no records matched the country, quarter and service filter. It does not establish zero service. `PARTIAL_MONTH_PRESENCE` means at least one expected month is absent. `PROVISIONAL_THREE_MONTHS_PRESENT` means all three months appear, not that every flight was reported.

`source_completeness_confirmed=False` and `reference_validated=False` are conservative defaults assigned by the preview builder. They are not calculated pass/fail results and are not updated by later aggregate checks. The extension years also lack matching historical reference rows. Use the separate comparison reports, coverage status and validation outputs; do not interpret these flags as evidence that every value is incorrect, or manually set them to True.
