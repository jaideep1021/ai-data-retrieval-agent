# Evidence-Grounded AI Data Retrieval Agent

## Commercial aviation development update — 12 November 2026

Read the [meeting progress report](docs/aviation-regulations/progress-summary-20261113.md)
and [aviation setup and status](docs/aviation-regulations/README.md).
This development update adds bounded discovery, evidence preservation, review tools,
optional OCR screening and navigation diagnostics. The final verified regulatory
CSV and full country/topic evaluation are **not complete**. Earlier release tags
and benchmark results remain unchanged.


A research project that investigates how an agent can retrieve missing or
questionable data from public sources, preserve supporting evidence, and decide
whether a candidate value can be accepted or should remain unresolved.

The project progresses from a Python Enhancement Proposal (PEP) metadata prototype
to autonomous source discovery and historical DOT airfare experiments. It separates
**finding a correct value** from **having sufficient evidence to accept it**.

**Current release: v0.3.1 — Week 3 research and documentation update.** Earlier releases remain available
as `v0.1.0` (Week 1) and `v0.2.0` (Week 2).

## Week 3 work and results

Week 3 evaluated the approved 30 DOT observations, investigated verification
failures, added Socrata as a third retrieval service, and developed an initial
literature-based formulation of the accept, retrieve or abstain decision.

Six observations supported development; the remaining 24 were evaluated after
freezing the core implementation. Each observation was tested through SerpApi,
Brave and Socrata: 18 development trials and 72 held-out trials in total.

| Held-out discovery service | Correct candidate | Retrieved record | Correctly accepted | Mean time | Search cost scenario |
|---|---:|---:|---:|---:|---:|
| SerpApi | 0/24 | 0/24 | 0/24 | 2.89 s | $1.20 |
| Brave | 24/24 | 24/24 | 24/24 | 8.98 s | $0.12 |
| Socrata | 24/24 | 24/24 | 24/24 | 8.59 s | $0 paid-search allocation |

These are results for a **specialized DOT workflow**, not a universal ranking of
search services. The successful path uses deterministic query templates, declared
DOT schema knowledge and structured records; it makes no Gemini calls. SerpApi
returned search results, but the bounded workflow did not locate an eligible
city-market dataset. Socrata searches a specialized public-data catalog.
Costs are allocation scenarios, not verified invoices; public API requests are
counted separately. All cases share a quarter and dataset family.

Verification now checks DOT publisher provenance, reporting period, market IDs
and field definitions. A separate audit of Week 2 identified 13 correct candidates
that were not accepted: 12 lacked a second usable grounded source and one had a
title-prefix conflict. The new authority policy is domain-specific; it does not
establish a general truth verifier or calibrated confidence model.

- [Comprehensive Week 3 report](docs/week3-report.md) · [Word version](docs/week3-report.docx)
- [Full experimental findings](docs/week3-structured-findings.md) · [Per-trial results](docs/week3-structured-results.json)
- [Method and reproduction commands](docs/week3-structured-retrieval.md)
- [Verification rejection audit](docs/week3-rejection-audit.md)
- [Literature review](docs/week3-literature-review.md) · [Proposed decision experiment](docs/week3-decision-experiment-plan.md)

The decision-policy experiment is proposed work; no simulator or learned stopping
policy is included. Earlier failed LLM/PDF pilots remain documented alongside the
successful structured experiment.

## Run the Week 3 workflow

For a fresh macOS/Linux checkout with Python 3.13 installed:

```sh
git clone https://github.com/jaideep1021/ai-data-retrieval-agent.git
cd ai-data-retrieval-agent
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-business.txt
python -m unittest discover -s tests
python evaluate_business.py check
python retrieve_record.py --record-id airfare-01 --provider socrata
```

The tests and input check are offline. The last command makes live public API
requests and saves evidence in a new ignored `runs/` folder; this Socrata path
requires no API key or Chromium browser. For exact released-code reproduction,
check out `v0.3.1` before installing. On Windows, create the environment with
`py -3.13 -m venv .venv` and use `.\.venv\Scripts\python.exe` for Python commands.

For SerpApi/Brave experiments, copy `.env.example` to `.env` **only if `.env` does
not already exist**, then configure your keys. LLM-based paths also require Gemini
access. Preserve existing keys and keep `.env` private. See the method guide for
paired-run commands and budgets. The original browser-based PEP workflow has
separate installation instructions below.

## Project versions and entry points

| Version | Scope |
|---|---|
| v0.1.0 — Week 1 | Eight-record PEP prototype, known-URL fallback and reference verification |
| v0.2.0 — Week 2 | Autonomous search, multi-source comparison, 20-record/60-trial PEP evaluation and DOT sample preparation |
| v0.3.0 — Week 3 | DOT experiments, structured retrieval, authority-aware checks, Socrata comparison, rejection audit and research formulation |
| v0.3.1 — Week 3 documentation | Improved project introduction, prominent Week 3 findings and current setup instructions; experiment code and results unchanged |

| Entry point | Purpose |
|---|---|
| `agent.py` | Preserved Week 1 PEP baseline |
| `autonomous.py` | Autonomous single-source discovery |
| `multisource.py` | Multi-source comparison with SerpApi or Brave |
| `evaluate.py` / `evaluation_report.py` | Week 2 benchmark and saved-results reporting |
| `prepare_business_data.py` | Prepare/replay the public historical airline sample |
| `business_agent.py` / `business_documents.py` | LLM business-data retrieval and HTML/PDF reading |
| `retrieve_record.py` / `structured_retrieval.py` | Single-record entry point and structured DOT retrieval |
| `evaluate_business.py` / `evaluate_structured.py` | Separate business experiments and offline reference scoring |
| `scripts/audit_week2_rejections.py` | Reproduce the audit using private saved Week 2 evidence |

## Code explanation and architecture

For the Week 2 implementation, read the [code and architecture guide](docs/week2-code-guide.md)
or the [weekly report with four task diagrams](docs/week2-report.md). Download the
repository and open `docs/walkthrough/index.html` for the offline interactive
walkthrough. This is a teaching simulation, not live execution; it requires no API
key or installation. The [Week 2 reproduction guide](docs/week2-reproduction.md)
provides its setup and commands. Week 3's workflow and verification rules are
explained in the [structured retrieval guide](docs/week3-structured-retrieval.md).

## Original Week 1 baseline guide

The setup below checks out **v0.1.0 intentionally** and does not contain the Week 2
or Week 3 files. For the current workflow, use the Week 3 setup above; for Week 2,
use its separate reproduction guide.

This Python program proposes corrections to a small CSV of Python Enhancement
Proposal (PEP) metadata. It searches for the official page, opens it in a browser,
asks Gemini for one value and a supporting quote, then checks that value against
the official PEP JSON dataset. It writes results for review; it never edits input data.

The eight input records contain deliberately missing or incorrect values. They are
an educational benchmark, not evidence of errors on python.org. This is a fixed,
sequential tool workflow, not a general autonomous research agent.

## Start here

1. Install Git and Python 3.13 (the baseline was verified with **3.13.5 on macOS ARM64**).
2. Clone this repository and create an isolated Python environment below.
3. Install the pinned packages and Chromium browser.
4. Run the offline tests; no API keys are needed for these.
5. Copy `.env.example` to `.env` and enter your own provider keys.
6. Review [scraping policy and concepts](docs/scraping.md), then try one PEP.

All commands run in the repository folder. Type terminal commands at the shell
prompt. Python statements such as `from urllib.robotparser import RobotFileParser`
belong in a `.py` file or the Python interpreter, **not directly in zsh/PowerShell**.

## Clone and install

### macOS or Linux

```bash
git clone https://github.com/jaideep1021/ai-data-retrieval-agent.git
cd ai-data-retrieval-agent
git checkout v0.1.0
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
python -m pip check
python -m unittest discover -s tests -v
cp .env.example .env
```

If your Python 3.13 executable is named `python3`, substitute that after checking
`python3 --version`. On supported Linux systems, browser system libraries may also
be needed: `python -m playwright install --with-deps chromium` (may request sudo).
The browser install is a separate step from installing the Python package.
See [Playwright browser installation](https://playwright.dev/python/docs/browsers).

### Windows PowerShell

```powershell
git clone https://github.com/jaideep1021/ai-data-retrieval-agent.git
cd ai-data-retrieval-agent
git checkout v0.1.0
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
Copy-Item .env.example .env
```

Using the executable directly avoids PowerShell activation-policy issues. For all
later `python` commands on Windows, use `.\.venv\Scripts\python.exe` instead.
Windows/Linux instructions are provided but were not locally executed; see
[verification](docs/verification.md) for actual checks and CI status boundaries.

`requirements.in` lists direct packages; `requirements.txt` pins the full resolved
environment. These are version pins, not a hash-verified supply-chain lock. Do not
upgrade packages individually when reproducing this release.

## Set up API access

Open `.env` in a text editor and replace the two placeholders:

```dotenv
SERPAPI_KEY=your_actual_serpapi_key
GEMINI_API_KEY=your_actual_gemini_api_key
GEMINI_MODEL=gemini-3.5-flash-lite
```

- Create/sign in to [SerpApi](https://serpapi.com/manage-api-key) and copy your API key.
  The package is `serpapi`, the [official Python client](https://serpapi.com/integrations/python).
- Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/apikey).
  Ensure your account/project can use the configured model and has quota.
- Never paste keys into Python source, screenshots, issues or commits. `.env` is ignored.
- Existing environment variables take precedence over `.env`. Only the specified
  `.env` file is loaded; parent folders are not searched. `--env-file PATH` supports
  an existing private file outside this repository.
- `gemini-3.5-flash-lite` preserves the working Week 1 configuration. Model
  availability can change; changing it is an experiment and should be documented.
- Live execution uses provider quotas and may incur charges. One full sample run
  requests eight searches and eight model extractions, plus provider SDK retries.

## Run and inspect

```bash
python agent.py --version
python agent.py --pep 8
python agent.py
```

Each command creates a **new** `runs/<UTC-time>-<unique-id>/` directory. For an easy
to-find output, choose a directory that does not exist yet:

```bash
python agent.py --pep 8 --output-dir runs/first-demo
python agent.py --input examples/records.csv --output-dir runs/all-eight
```

An existing output directory is rejected, preserving its results. Unlike the original
prototype, v0.1.0 does not overwrite a root-level `results.csv` or `evidence/`.
Results are saved after processing (including completed rows on an interruption
that unwinds Python); abrupt process termination or power loss can still lose rows.

For the single-record example, a successful run usually reports `Active` and `ACCEPT`
for PEP 8, plus verification flags set to true. The full example processes eight
rows. Exact values, search fallback frequency, model quotes and pass counts can
change. A historical eight-of-eight success does not promise future accuracy.

Open `runs/first-demo/results.csv` in a text editor or spreadsheet. Inspect the
supporting text in `runs/first-demo/evidence/pep_0008_<content-hash>.txt`. Keep generated output
local. Each run also includes:

| File | Purpose |
|---|---|
| `results.csv` | Proposed values, decisions, provenance and failure stages |
| `evidence/pep_NNNN_<content-hash>.txt` | Full visible page-body text, not original HTML |
| `reference.json` | The parsed official JSON snapshot used for comparison |
| `manifest.json` | Baseline version, model, UTC time, Python version, input and reference SHA-256 hashes |

The input hash identifies the full input file, even with `--pep`. Preserve your input
alongside the run if you need to replay it; the program does not copy private input.
Evidence hashes detect later file changes; they do not authenticate the publisher.
Evidence filenames include a content hash, so different captures of the same PEP
within a run retain separate files; identical captures reuse the same file.

Exit status is 1 for technical errors, otherwise 0. `REVIEW` is a completed decision,
so it does not produce a nonzero exit status. Always inspect decisions, not just exit status.

## Input and decisions

```csv
pep_number,attribute,current_value
8,status,
20,type,
257,created,
484,status,Draft
```

Required headers are `pep_number`, `attribute`, `current_value`. Leave the current
value empty when unknown. PEP IDs must be nonnegative integers; supported fields
are `title`, `status`, `type`, `created`. Bad rows become `ERROR` and later rows
continue; missing headers/empty input fail before API calls. `--pep` selects only
matching IDs, so malformed IDs outside that filter are not processed.

| Decision | Meaning |
|---|---|
| `ACCEPT` | Quote is present, value matches reference, and differs from input |
| `NO_CHANGE` | Same checks pass and input already matches |
| `REVIEW` | Quote missing/invented or candidate does not match reference |
| `ERROR` | A technical or validation stage failed; no factual conclusion |

Comparison collapses whitespace and ignores case. It does not normalize dates or
prove a quote supports the requested field. A quote from anywhere in the page can
pass the presence check. The webpage and JSON come from the **same publisher**;
they are not independent corroboration. `ACCEPT` is a proposed correction for human
review, not authorization to change a production dataset.

## Architecture and code walkthrough

![Architecture](docs/architecture.png)

The [SVG](docs/architecture.svg) and PNG open without a Mermaid extension. The editable source is
[architecture.mmd](architecture.mmd). GitHub also renders the diagram below.

```mermaid
flowchart TD
    A["records.csv<br/>PEP ID, attribute, original value"] --> B["Validate input and load PEP reference JSON"]
    B --> C["SerpApi search"]
    C --> D{"Official PEP result found?"}
    D -->|Yes| E["Search result"]
    D -->|No| F["Canonical URL fallback"]
    E --> G["Playwright browser retrieval"]
    F --> G
    G --> H["Save evidence text"]
    G --> I["Gemini Pydantic JSON extraction"]
    H --> J["Check literal evidence in page"]
    I --> J
    B --> K["PEP API reference value"]
    K --> L["Compare extracted vs reference"]
    J --> M{"Both checks pass?"}
    L --> M
    M -->|Yes, changed| N["ACCEPT"]
    M -->|Yes, unchanged| O["NO_CHANGE"]
    M -->|No| P["REVIEW"]
    G -.->|Failed stage| Q["ERROR"]
    I -.->|Failed stage| Q
    N --> R["results.csv + provenance"]
    O --> R
    P --> R
    Q --> R
```

1. `read_records`: read and validate CSV structure; apply the optional PEP filter.
2. `load_reference_data`: download official PEP JSON once; preserve a snapshot.
3. `discover_source`: search using SerpApi; accept only the exact official HTTPS
   host and PEP path, otherwise construct the known canonical PEP URL.
4. `fetch_source`: use Playwright Chromium, check status and final URL, capture
   visible text, save it and close the page even on failure.
5. `extract_attribute`: send the first 12,000 characters to Gemini; request
   `value` and `evidence_quote` with a Pydantic JSON schema. Treat page instructions
   as untrusted. Schema validation checks shape, not truth.
6. `verify_extraction`: compare the candidate to the reference and quote to the page.
7. `save_results`: write a CSV through a temporary file and atomic replacement.

Stage comments in `agent.py` follow this sequence. `scraping_demo.py` is a separate
teaching demonstration: static HTML parsing, browser text, then JavaScript changing
an in-memory page from `Loading...` to `Published`. Run `python scraping_demo.py`
after reviewing crawl policy; its first two steps access the public PEP page.

## Tests without paid APIs

```bash
python -m unittest discover -s tests -v
```

The offline suite mocks external services and covers URL restrictions, search
fallback, malformed input, all four decisions, HTTP/redirect/empty-page failures,
page cleanup, invalid model JSON, missing credentials, reference failures and CSV
persistence. One real-browser test is skipped by default. Enable it with:

```bash
RUN_BROWSER_TESTS=1 python -m unittest discover -s tests -v
```

PowerShell: `$env:RUN_BROWSER_TESTS="1"`, then run the same unittest command.
This browser test uses only local HTML and incurs no API charges. GitHub Actions
runs offline and browser tests on macOS, Windows and Ubuntu; a workflow definition
is not evidence of a passing remote run. See [verification](docs/verification.md).

## Troubleshooting

| Symptom | What to check |
|---|---|
| `zsh: command not found: from` | Put Python code in a `.py` file and run `python file.py`, or enter `python` first |
| `ModuleNotFoundError` | Use this repo's `.venv` Python; install `requirements.txt` there |
| Browser executable missing | Run `python -m playwright install chromium` with that same Python |
| Startup `FileNotFoundError` | Run in the repo root; check `--input` and required files |
| Startup `FileExistsError` | Choose a fresh `--output-dir`; old runs are intentionally preserved |
| Startup `RuntimeError` | Check both API keys are populated; check reference endpoint availability |
| Startup `ValueError` | Check CSV headers, nonempty rows and `--pep` filter |
| Startup HTTP/connection error | Check network/proxy/TLS and official JSON endpoint; do not disable TLS verification |
| `canonical_fallback` | Search failed or returned no exact official match; inspect `search_issue` |
| `ERROR`, validation | Check PEP number, supported attribute and reference availability |
| `ERROR`, retrieval | Check official page availability, browser install, redirects and network access |
| `ERROR`, extraction | Check Gemini quota/key/model, structured output support and response schema |
| `REVIEW` | Inspect quote, captured text and reference; do not silently accept it |
| 403/429 or quota exhaustion | Stop and check access/quota; retry later according to provider guidance |
| README diagram looks wrong | Open `docs/architecture.svg` in a browser or view README on GitHub |

External exception text is intentionally omitted from logs/CSV because SDK errors
can contain authenticated URLs. Error type and stage are retained. Startup failures
can occur before an output directory exists. A reference outage prevents verification
and stops the batch; record-level failures are retained in the CSV.

## Repository guide

```text
agent.py                 Pipeline with explanatory stage comments
scraping_demo.py         Static HTML vs browser/JavaScript teaching demo
records.csv              Original eight synthetic Week 1 records
examples/                Reusable input examples, including invalid records
.env.example             Placeholder configuration only
.gitignore               Secrets, environments and generated-output exclusions
requirements.in          Direct dependency pins
requirements.txt         Complete dependency version pins
VERSION                  Package development version; agent.py retains baseline version
CHANGELOG.md              Release history and compatibility notes
CONTRIBUTING.md           Safe update/release workflow
architecture.mmd         Editable diagram source
docs/architecture.svg    Readily viewable diagram
docs/scraping.md          Concepts, robots/terms and responsible use
docs/verification.md      Actual release verification record
tests/                   Offline contracts and optional browser smoke test
.github/workflows/       Cross-platform CI
runs/                    Local outputs only (ignored by Git)
```

## Limitations and next versions

This baseline has one domain, known URL patterns, one reference publisher, serial
processing, no autonomous planning and no general entity resolution. There is no
calibrated confidence score, automatic robots enforcement, caching, explicit crawl
delay, application-level retry/backoff, independent benchmark or semantic quote
validator. Browser redirects are checked after navigation, not blocked before
requests; this is not a sandbox for arbitrary user URLs. Temperature zero does not
guarantee deterministic model output. Live services, page content and models can
change despite pinned Python dependencies.

- **v0.1.0:** preserved specialized baseline and its original release tag.
- **v0.2.0:** autonomous discovery, multi-source comparisons,
  paired evaluation and public business-dataset preparation. See the Week 2 report.
- **v0.3.0:** DOT evaluation, structured-data access, publisher/context verification,
  Socrata comparison and an initial research formulation.
- **Proposed next work, subject to Dr. Sibdari's feedback:** adaptive query/schema
  handling, calibrated confidence and cost-aware stopping on new data.
  No prediction system or general truth verifier is claimed.

Use semantic versioning for the package. Keep the original agent's version label
at 0.1.0 while its implementation is frozen; development paths retain their recorded
development labels so historical run manifests stay interpretable. Do not rewrite
existing tags or benchmark results. See CONTRIBUTING.md for release practices.

No open-source license has been chosen for the project code yet; public visibility
does not establish broad reuse rights. Third-party data and dependencies retain
their respective terms. Discuss licensing before wider redistribution.

## References

- [Official PEP JSON API](https://peps.python.org/api/)
- [SerpApi Python integration](https://serpapi.com/integrations/python)
- [Playwright browser installation](https://playwright.dev/python/docs/browsers)
- [Gemini structured outputs](https://ai.google.dev/gemini-api/docs/structured-output)
- [Robots Exclusion Protocol, RFC 9309](https://www.rfc-editor.org/rfc/rfc9309.html)

### Deliverable 2: multi-source comparison

`multisource.py` adds separate page extraction, agreement/conflict reporting,
local evidence records, and selectable SerpApi/Brave search. SerpApi remains the
default. See [setup, commands and limitations](docs/multisource-step2.md) and
[actual test results and live findings](docs/multisource-step2-findings.md).
Agreement does not establish truth or independent corroboration. Both providers have completed live smoke tests; observed title-format conflicts
are documented in the findings. These capabilities are included in the combined v0.2.0 package.

### Deliverable 3: evaluation

Completed 20 distinct PEP observations across the baseline and two autonomous
configurations (60 live trials). See the [interpretation and caveats](docs/evaluation-step3-review.md),
[full findings](docs/evaluation-step3-findings.md), and
[reproduction protocol](docs/evaluation-step3.md). Candidate accuracy was 100% for
the specialized baseline, 5% for autonomous SerpApi and 90% for autonomous Brave.
All baseline records used canonical fallback; Brave's accepted-correct rate was
30%. These results do not establish general provider superiority. API costs are
labelled pricing scenarios, not verified charges.

### Deliverable 4: selected business dataset

Selected **historical airline pricing** after comparing it with a country-level
logistics dataset. Prepared 30 city-market pairs from the official DOT Consumer
Airfare Report, 2024 Q4, plus separate task inputs, reference answers and provenance
under `examples/business/`. See [dataset selection, definitions and reproduction](docs/business-dataset-step4.md).
This is public aggregate historical data, not current ticket quotes. The sample
reproduces offline. Week 3 evaluation results are linked below.

## Week 3 experimental DOT pipeline

The approved 30-observation sample is prepared for business-data evaluation.
Development used six observations; a subsequent frozen evaluation tested the other 24.
See the [experiment protocol](docs/week3-experiment-protocol.md),
[first pilot findings](docs/week3-dot-pilot.md), and
[retrieval repair and repeated pilot](docs/week3-retrieval-repair.md).
Start with the [completed structured retrieval findings](docs/week3-structured-findings.md)
and [method, verification rules and reproduction commands](docs/week3-structured-retrieval.md).
These Week 3 experiments are included in v0.3.0.

For the Week 3 reader and the complete current test suite, install the additional
pinned PDF dependency in the same environment:

```sh
python -m pip install -r requirements-business.txt
python -m unittest discover -s tests
python evaluate_business.py check
```

The check command makes no API calls. Live pilot commands and their budgets are
in the repair guide. Raw source documents, evidence and private correspondence
remain in ignored `runs/`. The original version tags and baseline commands remain
available.

For a single DOT record using the additional public retrieval service (no API key):

```sh
python retrieve_record.py --record-id airfare-01 --provider socrata
```

This command makes live requests and saves private evidence. It uses a declared
DOT schema and automatic template queries; it does not use Gemini.

Week 3 follow-up: [technical task status and meeting explanation](docs/week3-technical-task-status.md)
and [case-by-case Week 2 rejection audit](docs/week3-rejection-audit.md).

For the combined Week 3 research update, read the [short report](docs/week3-report.md)
or [Word report](docs/week3-report.docx), followed by the
[corrected literature review](docs/week3-literature-review.md) and
[proposed decision experiment](docs/week3-decision-experiment-plan.md).
