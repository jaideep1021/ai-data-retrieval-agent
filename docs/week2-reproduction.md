# Reproduce the Week 2 package

## Choose the right version

- `v0.1.0` is the existing historical baseline tag. It does not include Week 2 files.
- v0.2.0 contains the combined Week 2 work.
- `agent.py --version` still reports 0.1.0 intentionally: that implementation is
  frozen. autonomous.py and multisource.py retain their recorded experiment labels.

Clone and select the version:

```sh
git clone https://github.com/jaideep1021/ai-data-retrieval-agent.git
cd ai-data-retrieval-agent
git checkout v0.2.0
```

## Install from the selected checkout

macOS/Linux, Python 3.13:

```sh
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
python -m pip check
python -m unittest discover -s tests -v
```

Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Use the Windows environment's executable in place of `python` below. These are
cross-platform instructions, not claims that Windows/Linux were tested locally.
For Linux browser system dependencies see the baseline README. To include the
real local Chromium test, set RUN_BROWSER_TESTS=1 (PowerShell:
`$env:RUN_BROWSER_TESTS="1"`). It opens local HTML, not a paid API.

Virtual environments are local and are not shipped. Do not overwrite an existing `.env`. If none exists, copy
`.env.example` to `.env`, then configure Gemini and the selected search provider.
SERPAPI_KEY is required for the baseline and SerpApi modes; BRAVE_SEARCH_API_KEY
is required for Brave mode; GEMINI_API_KEY is needed for all agent runs. Keep keys
local. Public dataset preparation and offline tests do not require them.

## Choose an experiment

```sh
# Original specialized baseline, one record
python agent.py --pep 8 --output-dir runs/baseline-check

# Single-source automatic discovery (SerpApi)
python autonomous.py --entity "PEP 703" --attribute title

# Multi-source automatic comparison (select provider explicitly)
python multisource.py --entity "PEP 703" --attribute title --provider brave

# Full benchmark: 20 records x three configurations, paid-service calls
python evaluate.py run --output-dir runs/new-evaluation --model-interval 7

# Recompute an existing local evaluation without API calls
python evaluate.py summarize --output-dir runs/new-evaluation
python evaluation_report.py runs/new-evaluation --output-dir runs/new-evaluation/report

# Download and prepare the selected public historical dataset; no key needed
python prepare_business_data.py --output-dir runs/new-airfare-sample

# Exact offline replay of that saved source capture
python prepare_business_data.py --from-run runs/new-airfare-sample --output-dir runs/new-airfare-replay
```

Use new output directories each time. API/model outputs and refreshed historical
data may differ from the saved results. The original 60-trial run took about
22.5 minutes with seven-second model pacing. Rate limits vary by account; other
clients can consume shared quota. A 429 stops the evaluator and preserves completed
trials. Inspect the completion count; a partial run is not a full benchmark.

## Read results honestly

The original baseline verifies against official reference values. Automatic
comparison reports agreement/conflict/insufficiency; it does not guarantee truth.
Exit 2 in multi-source mode is a completed review-needed result, not necessarily a
crash. See the mode-specific docs for exit meanings.

The repository includes reviewed evaluation rows and summaries in
`docs/evaluation-results.json`, so the reported numbers are inspectable without
paid calls. Raw captures are intentionally not published: a clone cannot claim
independent verification of their contents or replay them unless separately
provided through an appropriate channel. The 30-row public airline sample and its
provenance are included under `examples/business/`; agent tasks and reference
answers are separate. Do not pass the sample or answer key to an agent during a
blind evaluation.

See [Week 2 report](week2-report.md) for interpretation and
[release review](release-review-v0.2.0.md) for the precise checks actually performed.
