# Deliverable 1: autonomous search, single-record milestone

Status: experimental development version `0.2.0-dev.1`. The release tag `v0.1.0`
and original `agent.py` are preserved. This is not completion of the five-deliverable
research plan. Multi-source comparison, an alternative provider, the 20–50-record
evaluation and business dataset selection remain separate deliverables.

## Objective

Given an entity and attribute, generate a search query, choose a URL from actual
search results, retrieve it and propose a value with captured supporting evidence.
No source URL, fixed domain, canonical URL template or reference answer is supplied.
The first development example is the title of PEP 703.

## Run

Use the baseline's pinned environment. No new packages or API keys are required.

```bash
python autonomous.py --entity "PEP 703" --attribute title
```

To use an existing private key file and an explicit new output directory:

```bash
python autonomous.py --entity "PEP 703" --attribute title \
  --env-file /path/to/private/.env --output-dir runs/autonomous-demo
```

For Windows, put the command on one line and use your virtual environment's Python.
The `.env` fields remain `GEMINI_API_KEY`, `SERPAPI_KEY` and `GEMINI_MODEL`.
Each output directory must be new. Credentials and `runs/` remain ignored by Git.
The original command `python agent.py --pep 703` still runs the assisted baseline.

## What happens

1. **Generate:** Gemini receives only entity and attribute, then generates one query.
   The first query rejects URLs, domains and `site:` restrictions. The entity must
   be present. A revised query may use only domain terms observed in the first
   search results (including a conservative parent-domain heuristic). No domain
   or source URL is seeded in code or supplied by the operator.
2. **Discover:** SerpApi returns up to ten organic candidates. Titles, URLs and
   snippets are retained for inspection. There is no canonical fallback.
3. **Select:** Gemini picks an index from those candidates, favoring direct,
   relevant publications. An invalid index is rejected; a null choice abstains.
4. **Retrieve:** a bounded HTTPS request obtains static HTML/text. BeautifulSoup
   removes script/style/navigation content and extracts main/article text when
   available. This experimental path does not execute JavaScript.
5. **Extract:** Gemini receives the first 12,000 characters of captured text, entity
   and attribute, and returns a value, value quote and entity quote. Search snippets,
   current value and reference data are not provided to this extraction call.
6. **Check:** normalized quotes must occur in the supplied text, the value must occur
   in the value quote, and the entity identifier must occur in the entity quote (optional metadata
   colon punctuation is accepted, while different numeric IDs are rejected).
7. **Save:** write the result, evidence hash, elapsed time, model-call usage when
   available, selection explanation, candidate list and robots-check observations.

The current value is logged for provenance only; it does not steer the answer.
If the first search is empty or lacks a primary publication, the agent generates
one distinct revised query using the failure reason and discovered domains.
Repeated queries and unobserved domains are rejected.
There are at most five application-level model calls, two search calls and one
selected source fetch. Robots checks and bounded redirects add HTTP requests.
SDK-internal retries may add provider attempts. No monetary cost estimate is made
in this milestone; usage is recorded as a foundation for later evaluation.

## Output and interpretation

`runs/<run>/result.json` contains the structured audit record. The accompanying
`evidence_<hash>.txt` contains extracted page text, not raw HTML. A failed run still
writes a result when it reaches the run function; startup/configuration failures
can occur before a run folder exists. Existing run folders are never overwritten.

| Decision | Meaning | Exit status |
|---|---|---:|
| `SUPPORTED_CANDIDATE` | Mechanical value, quote and entity checks passed | 0 |
| `INSUFFICIENT_EVIDENCE` | No relevant result or missing/unsupported extraction | 2 |
| `ERROR` | Query, provider, selection, retrieval or parsing failure | 1 |

`SUPPORTED_CANDIDATE` is not equivalent to the baseline's reference-checked
`ACCEPT`. A quotation can occur on a page without supporting the intended meaning.
The checks do not prove publisher identity, semantic correctness or independent
corroboration. Source selection is model judgment and may choose a poor source.
No claim of general accuracy can be based on this one development example.

## Retrieval boundaries

Only HTTPS, standard port 443, credential-free URLs resolving to public IP
addresses are accepted. Redirect destinations are checked before each request.
At most three redirects and 2 MB of decoded response bytes are allowed per read.
Only HTML and plain text are supported. JavaScript-only sites and PDFs may fail.

The retriever checks robots.txt for each destination origin. It allows missing
404/410 policies, honors disallow rules, and stops on other policy errors. Sites
requesting crawl-delay/request-rate scheduling are deferred rather than silently
ignoring that requirement. This conservative implementation is not a complete
RFC 9309 crawler. Robots permission does not replace terms or license review.

Public-IP checks are a best-effort guard, not a security sandbox. DNS is resolved
again by the HTTP client and can change; hardened deployment needs controlled
network egress. Search metadata and retrieved text remain untrusted. Avoid private
or sensitive entities because query/extraction inputs are sent to external APIs.
Exception strings are omitted because SDK errors can contain authenticated URLs.

## Tests

```bash
python -m unittest discover -s tests -v
```

The new tests cover generated-query use, absence of oracle inputs, abstention,
invented selection indexes, evidence mismatch, provider/JSON failures, private
destinations, redirect validation, robots policy failures and run preservation.
All use mocks and synthetic text. The baseline tests remain unchanged.

## What is intentionally next

This milestone uses at most two queries and one selected source. It does not yet
retry retrieval/extraction failures, compare sources, switch providers, estimate monetary costs or run a large
benchmark. Model pretraining may already contain PEP facts; withholding runtime
answers does not establish that the task is unseen. Follow-up evaluation should
measure the limits rather than assume full autonomy.

See [development findings and actual verification](autonomous-step1-findings.md).
Pause for discussion after this deliverable before starting multi-source work.
