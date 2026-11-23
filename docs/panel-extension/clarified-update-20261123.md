# Africa aviation and trade dataset update

**v0.5.1**

The extension contains 364 observations for 14 African countries, covering 2020 Q1–2026 Q2. Each observation represents one country over three months. The supplied 2015–2019 dataset and original downloads remain unchanged. The full 2009–2019 dataset was unavailable, so this delivery is a separate extension rather than a combined historical workbook.

## Work completed

- Processed aviation and U.S. trade data for all 14 countries. Scheduled services are the main aviation measure; all-service comparisons are retained separately.
- Retained both the number of distinct airlines and the number of detailed source records. These measure different things and should not be treated as interchangeable.
- Applied the agreed definitions: U.S. versus foreign carriers, U.S. fuel prices, fixed country income groups, and U.S. residents born in each African country.
- Included available GDP, population, exchange rates, purchasing power parity (PPP), tourism and unemployment data. Added an indicator showing where scheduled nonstop flights were observed.
- Preserved missing values, source links, download dates and processing rules. Annual values repeat within their year to fit the quarterly layout; they are not newly measured quarterly values.

## Data available

Counts below are populated country-quarter observations out of 364, not accuracy scores.

| Measure | Available |
| --- | --- |
| Imports, exports and total trade | 364 each |
| Scheduled seats and passengers | 203 each |
| All-service seats and passengers | 209 each |
| GDP, population and GDP PPP factor | 336 each |
| U.S. fuel prices | 364 for each measure |
| U.S. residents born in each African country | 232 |
| Destination unemployment / U.S. unemployment | 180 / 350 |
| Tourism arrivals / compatible air-connectivity index | 180 / 0 |

## How to interpret the workbook

**PPP** is a conversion factor used to compare purchasing power across countries. GDP-based and consumption-based PPP are kept separate. **Foreign carriers** means all non-U.S. airlines, not only African airlines.

**NO_SELECTED_RECORDS** means no aviation records matched the country, quarter and service category. It does not prove that no flights operated. The two **False** validation flags are default markers: they do not mean that every value failed a check. They indicate that complete source reporting or a matching reference check has not been established by that field.

## Checks and remaining limitations

The saved-data rebuild reproduced the prepared results, and the exported workbook matched its underlying data. All 304 release tests passed. These checks establish processing consistency, not certainty about every published source value.

Unavailable values remain blank rather than being estimated or replaced with zero. October 2025 U.S. unemployment is unavailable, so its fourth-quarter average is also blank. Tourism, immigration and recent annual data have gaps; a compatible air-connectivity index was not obtained. Employment counts were not derived from unemployment rates. Some historical trade dates and GDP/PPP definitions still differ from the supplied five-year dataset.

The package is ready for review and later missing-data research. Collection used researcher-configured programs and official sources; this exercise does not establish fully autonomous retrieval.

Sources: BTS aviation data; U.S. Census trade and American Community Survey; World Bank; U.S. Energy Information Administration; Bureau of Labor Statistics; and preserved UN Tourism files. Detailed source links and download dates accompany the local data.
