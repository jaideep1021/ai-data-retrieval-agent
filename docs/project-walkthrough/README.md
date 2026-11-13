# Connected architecture and implementation guide

Open index.html locally in a browser. GitHub displays source rather than running the page. No server, API key or additional package is needed for the viewer. All file loading is local. No credentials or raw run evidence is bundled.

## Follow this sequence

| Order | Diagram tab | Explain | Main code | Evidence boundary |
|---|---|---|---|---|
| 1 | Week 1 baseline | Search, read, extract, verify, save | agent.py | Canonical fallback and reference assistance |
| 2 | Autonomous search | Generate queries without supplied URLs | autonomous.py, search_providers.py | Bounded autonomy, no guarantee of discovery |
| 3 | Multi-source evaluation | Compare claims and measure outcomes | multisource.py, evaluate.py, evaluation_report.py | Agreement is not proof of independence |
| 4 | Structured DOT | Match schema, period, market and field | retrieve_record.py, structured_retrieval.py, evaluate_business.py | Specialized successful workflow; no Gemini |
| 5 | Commercial aviation | Discover documents and audit evidence | aviation_agent.py, aviation_selection.py, business_agent.py, commercial_aviation.py | Latest trial: no verified target events |
| 6 | Optional OCR | Read a bounded subset and record coverage | optional_pdf_ocr.py, aviation_review_server.py | Screening/review, not accepted event extraction |

Use Previous/Next or click a stage. Read Input → Action → Output, then the What to explain paragraph. Expand implementation only when needed. Selecting a function in the explorer immediately opens the code. Search covers core modules, not every test/helper in the repository.

## Evidence viewer
Load an aviation result.json, OCR ocr-manifest.json, or compatible structured result using the local file picker. Select a recorded item to inspect its actual fields. The viewer is read-only; it does not submit human labels. Files are not uploaded. This is a recorded-output viewer, not a full temporal replay: it does not invent timestamps or reconstruct unlogged calls. Other JSON formats are shown as raw data without specialized interpretation.

The explanation animation is independent of evidence loading. It does not mean the agent is running. Live execution must be launched separately in a terminal; the page does not monitor the process. Automatic live stage highlighting is not implemented.

## Live demonstration
Activate the project Python environment, then choose one command shown on the relevant tab. Use a new output folder. Commands for PEP/autonomous/multisource/aviation can use paid or credited APIs; structured Socrata uses public network access. Do not run a complete benchmark merely to demonstrate the architecture. Preserve failed results and use a clearly labelled saved example if a service is unavailable.

## Rebuild source snapshots
From the repository root:

```sh
python scripts/build_project_walkthrough.py
```

The builder parses source locations and docstrings, validates mapped symbols, and embeds code snapshots with SHA-256 identifiers. Rebuild after source edits. template.html is the authoring template; open index.html for the working viewer.

## Presentation plan
Allow 2 minutes for the research question, 3 for stages 1–3, 4 for DOT and one live example, 5 for aviation/OCR recorded evidence, and 3 for limitations and next evaluation. Keep historical results, live attempts, diagnostic replays and proposed work distinct. Consult the progress report for metrics; the viewer makes no new performance claim.
