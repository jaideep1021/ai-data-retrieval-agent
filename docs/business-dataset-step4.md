# Deliverable 4 — selected business dataset: historical airline fares

**Decision:** use one airline-pricing dataset, not both airline and supply-chain
implementations. Prepared on 2026-10-28 for discussion with Dr. Sibdari.
This identifies and prepares the next research dataset; it does not assert that
the existing autonomous pipeline is validated for business data.

## Candidate comparison

| Candidate | Fit and access | Main limitation | Decision |
|---|---|---|---|
| DOT Consumer Airfare Report, Table 1 | Official historical market fares, traffic and distance; public JSON API; manageable quarter-sized data; documented field meanings | Aggregate city markets, not live quotes or individual tickets | Selected |
| BTS DB1B / DB1C ticket-level data | Rich itinerary/fare information and official documentation | Larger files and more complex units; collection changed in July 2025 | Possible later extension |
| World Bank Logistics Performance Index | Public country-level logistics indicators; catalog lists CC BY 4.0 | Survey-based national logistics performance, not shipment costs, inventory or delivery transactions | Considered, not downloaded or implemented |

World Bank catalog: https://datacatalog.worldbank.org/search/dataset/0038649/logistics-performance-index
BTS collection overview: https://www.bts.gov/topics/airlines-and-airports/origin-and-destination-survey-data

The DOT aggregate table is a closer fit to a small, checkable airline-pricing
retrieval exercise. This is an engineering/research fit decision, not a claim
that airline pricing is intrinsically more valuable than supply-chain research.

## Selected source and scope

- Publisher: U.S. Department of Transportation, Office of the Assistant Secretary
  for Aviation and International Affairs (source metadata attribution).
- Dataset: **Consumer Airfare Report: Table 1 — Top 1,000 Contiguous State City-Pair Markets**.
- Dataset ID: `4f3n-jbg2`.
- Landing page: https://data.transportation.gov/d/4f3n-jbg2
- Metadata/schema: https://data.transportation.gov/api/views/4f3n-jbg2.json
- Public API: https://data.transportation.gov/resource/4f3n-jbg2.json
- Definitions: https://www.transportation.gov/policy/aviation-policy/air-fare-information-consumers
- Fixed period: **2024 Q4**. This is intentionally historical, not the latest quarter.
- Retrieved population: **1,000 rows**. Sample: **30 unique city-market pairs**.
- Selection: sort by numeric city-market IDs, sample without replacement with
  Python `random.Random(20261028)`, then sort the selected records by IDs.
- Data representation: JSON records with decimal strings preserved. No spreadsheet
  or rounding is required to reproduce the sample.

The fixed quarter predates the July 2025 transition from quarterly 10% DB1B
collection to monthly 40% DB1C collection described by BTS. Selecting one period
avoids mixing those regimes in the starter sample. Later trend analysis would
need explicit treatment of that change and any other methodological revisions.

## Meaning of the data

Each row describes a city-market pair for the selected quarter. Cities can group
multiple airports. Do not reinterpret the row as a particular airport pair,
individual flight, nonstop-only ticket, or current purchasable offer. Match the
source city-market identifiers and time period before comparing figures.

DOT describes the fares as averages of each-way prices paid, including taxes and
airport fees and paid first-class travel; free tickets and optional ancillary
charges are excluded. Distance is the reported nonstop market distance, not
necessarily the flown itinerary distance. Passenger figures are daily averages,
which explains their fractional values. The report is suitable for historical
market questions, not live booking recommendations.

### Data dictionary

| Field | Meaning and representation |
|---|---|
| record_id | Local sample identifier; not a DOT source ID |
| year, quarter | Source reference period, preserved as strings in sample |
| citymarketid_1, citymarketid_2 | DOT city-market identifiers, not airport codes |
| city1, city2 | Source city-market labels |
| nsmiles | Nonstop market distance in miles; decimal string |
| passengers | Average passenger trips per day; decimal string |
| fare | Overall average each-way market fare in USD; source precision retained |
| carrier_lg | Code for carrier with largest market share; no unverified name mapping added |
| large_ms | That carrier's market share as a fraction, not a percentage |
| fare_lg | That carrier's average fare, USD |
| carrier_low | Carrier meeting the report's lowest-average-fare carrier definition |
| lf_ms | That carrier's market share as a fraction |
| fare_low | That carrier's average fare, USD; not the cheapest ticket offered |

The lowest-fare carrier has a market-share eligibility rule and exceptions;
it is not simply the airline advertising the cheapest seat. Consult DOT's full
definition before using these fields for comparisons. An average market fare
can be below this carrier's average, so the validator does not impose
`fare >= fare_low` or use it as an automatic contradiction test.

## Prepared repository files

All five reviewed files under `examples/business/` contain public aggregate data
or derived tasks, not private user records:

- `sample.json`: 30 selected records, original decimal precision, 15 source fields
  plus the local record ID. This contains reference values; do not feed it to an
  agent in a blind evaluation.
- `task-inputs.json`: 30 proposed questions, city-market identifiers, quarter,
  attribute and unit. No expected answer or source URL supplied to the agent.
- `answer-key.json`: evaluator-only values, units and proposed tolerances.
- `provenance.json`: source URLs, exact query URL, capture time, sampling seed,
  license marker, source-response hashes, and output hashes.
- `sample-summary.json`: simple size/range checks; explicitly marks business-agent
  evaluation as not performed.

Raw source rows and metadata are saved only in the ignored local folder
`runs/business-dataset-20261028/`. No private data, secrets, or full raw web evidence
are copied into the reviewed examples. This is a deliberate exception for a small
reviewed public sample, not permission to commit future customer datasets.

## Prepared task examples

The sample includes 10 proposed questions each for average fare, average daily
passenger trips and market distance, with reference answers stored separately.
The answer key records proposed tolerances of $0.01 for fare, 0.01 trips/day for
traffic and exact distance. A business-domain numeric scorer and live agent
evaluation have not been implemented.

## Verification and evidence limits

The public API is a reference source, not independent corroboration. Its PDF
report, dashboard, and API may be different presentations of the same DOT data.
Checking them can establish cross-format consistency, but does not supply
independent measurements. The official source is also not infallible and may be
revised; preserve the captured bytes/hashes and quarter.

The PEP pipeline must be adapted before these tasks can be scored fairly. Needed
work includes structured-data handling, robust numeric/unit matching, and
explicit market/period alignment. Neither the dataset sampler nor the prepared
questions claim those capabilities are complete. Preserve the existing PEP
benchmark results while designing the next experiment.

## License, attribution and ethical use

The fetched dataset metadata reports `licenseId: USGOV_WORKS`. Preserve the DOT
attribution and the dataset/definition links when sharing the sample; no DOT
endorsement is implied. The preparation tool stops if that license marker or
dataset identity changes, requiring review before publishing a revised sample.
This records the source's stated reuse metadata, not a legal opinion covering
other websites, third-party material, logos, or future commercial use.

Access uses the published public API with bounded requests and timeouts; no API
key, login, paid service, access-control bypass, or personal ticket data is used.
If future sources require scraping, review their terms and robots policies and
keep the existing retrieval safeguards. Raw outputs stay local.

## Reproduction

From the project root, activate the environment described in the main README.
No new dependency or secret is required.

```sh
python prepare_business_data.py --output-dir runs/my-airfare-sample
python prepare_business_data.py --from-run runs/my-airfare-sample --output-dir runs/my-airfare-replay
python -m unittest discover -s tests -v
```

Every output directory must be new. The first command downloads one fixed-quarter
population and metadata; the second performs **no network access** and verifies
the raw hashes before rebuilding. The source may revise historical data, so a
new download is not guaranteed to match the recorded snapshot. Offline replay
of the captured raw responses is the exact reproduction path. Keep the published
sample/provenance unchanged when comparing later revisions.

The tool rejects wrong periods, missing fields, negative/non-finite numeric
values, invalid shares, duplicate or reversed city pairs, and unexpected counts.
It refuses to silently filter bad rows. HTTP failures, changed licensing, or a
population reaching the 2,000-row cap stop preparation for review.

## Actual checks performed

- Downloaded the official 2024 Q4 population: 1,000 records, all validated.
- Produced 30 unique pairs and 30 questions: 10 fare, 10 traffic, 10 distance.
- Sample fare range: **$152.986549–$401.5144172**; distance range: **304–2,279 miles**.
- Replayed the captured data offline; selected output files matched byte-for-byte.
- Full test suite: **67 passed**, including Chromium and seven new data-preparation
  tests covering determinism, invalid data, duplicate pairs, bounds, replay,
  tampered raw data, existing output protection, and license changes.
- No LLM/search-provider calls, business prediction results, or new API charges
  were required for preparation. No Windows/Linux execution was claimed.

## Limits and discussion

Thirty randomly selected markets from one quarter do not represent all air travel,
all fare classes, smaller markets, international routes, or all time periods.
The sample cannot train a credible price-forecasting model or establish a causal
relationship between airline concentration and fares. Do not average the sample's
market fares and call the result a national passenger-weighted fare.

Discuss with Dr. Sibdari whether the next research objective should be historical
fact retrieval, source-comparison reliability, or a later predictive task. This
sample supports the first two as a controlled starting point. The consolidated
Week 2 findings are in week2-report.md.
