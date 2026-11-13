# Autonomous aviation demo: code walkthrough

This describes the Part 2 comparator. The CLI now uses the Part 3 path described
in [the verification guide](verification-guide.md); original results are preserved.

## Run and inspect

From the repository root, activate the existing environment with the dependencies
in requirements-business.txt installed. Keep credentials in the ignored .env file.
Run one development task, using a new ignored output directory each time:

```sh
python aviation_agent.py --task-id KEN-aviation_safety_changes --output runs/aviation-demo-new
```

This command uses live search/Gemini allowances. It is capped at two searches per
provider, three candidate document attempts per provider and thirteen Gemini HTTP
attempts total (one shared planning allowance plus six per provider). Retries count;
a retry during planning can reduce the remaining batch capacity. Requests are
sequential and at least seven seconds apart. Other applications using the same
project can still cause rate limits. No billing settings are changed.

Read manifest.json and model-usage.json for run status and actual usage, then each
provider's result.json for queries, search results, documents, candidates and errors.
Raw document bytes and extracted text remain local under runs/. Do not publish
these files or credentials. A candidate is never a human-verified event by default.

## Function-by-function explanation

| Definition | Why it exists and how it works |
| --- | --- |
| Task | Accepts country, topic and period fields; rejects extra answer/URL fields before any model call. |
| Plan | Requires two queries. The same plan goes to both providers to reduce query confounding. |
| Selection | Requires indices into observed results. The model cannot supply arbitrary URLs. |
| Event | Represents one proposed event with separate announcement/effective dates and quotations. Missing dates may be null. |
| Extraction | Allows zero to six events per document; a page need not contain an event. |
| make_plan | Sends only task context to Gemini, then rejects URL/domain restrictions in the generated initial queries. |
| run | Searches, selects observed links, reads bounded documents, requests structured events and saves successes/failures. |
| audit_event | Checks country, valid full-date syntax and literal quotation occurrence. Leaves semantic/legal interpretation to human review. |
| main | Loads local credentials, creates the paced model client, runs one task on SerpApi then Brave, and writes usage and source hashes. |

## Example execution flow

The Kenya safety task contains no known rating, event date or source URL. Gemini
generates two searches. Each provider returns candidates. Gemini selects observed
indices; the existing BusinessRetriever checks public destinations, robots rules
and content limits. A readable page is saved before extraction. Gemini proposes
events from up to the first 24,000 characters. audit_event flags unsupported quotes
or invalid dates. Every surviving candidate still needs a reviewer to establish
publisher authority, date meaning, historical applicability and duplicates.

Document links observed on a page may enter the next selection round, but this
first demo has no unrestricted recursive crawl. Three failed fetches exhaust the
document budget. Empty search results, blocked robots and unreadable PDFs remain
visible outcomes; they are not evidence that no regulation existed.

## Reused code and research limits

SearchProvider supplies the existing SerpApi/Brave adapters. BusinessRetriever and
business_documents retain HTML/PDF handling. StructuredModel validates model JSON;
PacedModels supplies recorded request limits and transient retry policy. The new
module changes no existing pipeline or release version.

This is a development demonstration, not a provider ranking or a final benchmark.
Provider order is fixed in this demo; later comparisons should rotate order.
The first 24,000 characters can omit relevant sections; saved full text allows
review of this limitation. Scanned/long PDFs can fail. Authority classification,
semantic date checks, conflict resolution and verified CSV export are the next
verification deliverable. Normalized quotation matching alone does not establish
truth or date interpretation. The model has no reference-answer access, but that
does not prove it has never seen these public facts in training.
