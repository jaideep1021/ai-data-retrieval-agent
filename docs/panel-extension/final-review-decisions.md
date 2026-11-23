# Dataset extension: applied decisions and limitations

Updated 23 November 2026. This replaces the earlier open-decision checklist. The published v0.5.0 snapshot is unchanged.

| Item | Applied treatment |
| --- | --- |
| Service scope | Scheduled F is primary; all-service F/G/L/P comparisons remain separate. Both airline-count measures are retained. |
| Missing aviation | Remains missing. Nonstop is 1 only with positive observed scheduled departures. No returned activity does not prove zero service. |
| Carrier labels | Foreign (all non-US) and US counts/seats, retaining the existing dated BTS classifications. |
| Fuel | US fuel accepted. BTS quarter-end and EIA mean monthly spot prices remain distinct, in USD/gallon. Empty African fuel-cost placeholder removed. |
| Immigration | ACS US residents born in each country, in persons, with margins of error and missing values preserved. |
| Income | Each country's constant label from the supplied 2015-2019 reference is fixed throughout the extension. |
| Unemployment | Destination national annual estimates and US seasonally adjusted monthly rates averaged across three months. The US quarterly rate is shared across destinations. |
| PPP | GDP conversion factor retained; household/NPISH consumption conversion factor added separately. Both use LCU/international dollar. Historical definition remains qualified. |
| Trade | Actual Census dates retained, USD millions. Historical date discrepancies remain documented without shifting data. |

Remaining limitations: compatible connectivity levels and some tourism, immigration and national unemployment observations are unavailable. October 2025 BLS unemployment is missing due to the lapse in appropriations, so Q4 2025 is blank. Annual values repeat within their source year, not as measured quarterly observations. No 2026 annual values are inferred. GDP/PPP historical definitions and source revisions are not fully reconciled. Employment counts are not derived from unemployment rates.

The full historical workbook is unavailable, so a complete 2009-2026 merge is not claimed. Raw downloads and the five-year reference remain unchanged. Published source estimates are retained, but the project does not impute missing values. Collection is researcher-configured, not an autonomous-agent benchmark.

See [the clarified update](clarified-update-20261123.md) and [README](README.md).
