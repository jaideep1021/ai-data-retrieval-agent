# Week 3: DOT retrieval, verification and service comparison

Recorded 5 November 2026 US Eastern (run timestamps use 6 November UTC).
Unreleased technical findings for Dr. Sibdari. Literature review and sequential
decision modeling are Jaideep's separate contribution and are not claimed complete.

## Question and experiment

Can the system recover missing or questionable values for the approved 30 DOT
city-market observations without receiving the answer or a source URL?
The sample covers 2024 Q4: 10 fares, 10 daily passenger counts and 10 distances,
with 15 missing and 15 deliberately questionable values. Six cases were used for
development and the remaining 24 for a subsequent frozen evaluation. Each case
was tested with SerpApi, Brave and the additional Socrata Discovery service.

The final implementation automatically generates deterministic domain-template
queries, discovers dataset identifiers, checks metadata and retrieves exact rows.
It does not use Gemini. It assumes a known DOT field schema, supplied market IDs,
units and a configured publisher trust registry. Neither source identifiers nor
expected values are supplied to the agent. The offline scorer alone opens the
answer key. This is a domain-specific automatic retrieval workflow, not a fully
general agent that learns new dataset schemas autonomously.

## Held-out results: 24 observations per service

| Discovery service | Correct candidate | Retrieved record | Correctly accepted | Mean time | Search cost scenario |
|---|---:|---:|---:|---:|---:|
| SerpApi | 0/24 (0%) | 0/24 (0%) | 0/24 (0%) | 2.89 s | $1.20 |
| Brave | 24/24 (100%) | 24/24 (100%) | 24/24 (100%) | 8.98 s | $0.12 |
| Socrata Discovery | 24/24 (100%) | 24/24 (100%) | 24/24 (100%) | 8.59 s | $0 paid-search allocation |

There were no incorrect acceptances. Accepted precision is 100% for Brave and
Socrata and undefined for SerpApi because it accepted nothing. SerpApi left all
24 unresolved. Its short runtime reflects early failure, not faster successful
retrieval. Retrieval here means a structured record was obtained, not merely that
a search request returned links. Fare and passenger accuracy use the predeclared
absolute tolerance of 0.01; distance requires an exact match.

SerpApi made 48 search and 24 public API requests; Brave made 24 search and 144
public API requests; Socrata made 168 public API requests, including catalog calls.
There were zero Gemini calls. Latency includes deliberate API pacing. Costs use
allocation assumptions of $0.025/SerpApi search and $0.005/Brave search, not verified
charges or a claim about the user's free credits. Public API calls are counted
separately; no paid search charge is assigned to anonymous Socrata access.

Development results were consistent but are not pooled with the held-out results:
SerpApi 0/6 correct, Brave 6/6 and Socrata 6/6. Mean times were 4.64, 10.42 and
9.45 seconds respectively. Development search-cost allocations were $0.30, $0.03
and $0. Total structured experiment: 90 trials, 90 search requests, 420 public API
requests and zero model calls; total search allocation $1.65.

## Why retrieval and verification differed

Earlier LLM/PDF pilots retrieved relevant material but recovered no values within
the strict scoring tolerances. Failures included airport versus city-market
aggregation, wrong reporting quarter, model/service errors and rounded PDF values.
For example, 3,109 passengers/day differs from 3108.913043 by about 0.087, exceeding
the fixed 0.01 tolerance. Fixing comma parsing did not make that answer correct.
The [original pilot](week3-dot-pilot.md) and [repair experiment](week3-retrieval-repair.md)
preserve those outcomes; they have not been overwritten by the new results.

The structured adapter obtains full-precision records. It checks period, both
market IDs, field/unit interpretation, schema and publisher metadata. Airport-pair
records are rejected. In this experiment SerpApi surfaced the official airport-pair
table rather than an eligible city-market table within the bounded search path;
its authority alone therefore did not justify acceptance. These outcomes describe
these queries and adapter limits, not general superiority of one search company.

Two verification policies were applied to the same captured structured evidence.
The agreement comparator accepted zero cases for every service: matching DOT
Table 1 and Table 6 rows were duplicates, not independent corroboration. The
experimental authority-aware policy accepted the matching original-publisher
record for all 24 Brave and all 24 Socrata cases. It requires explicit publisher,
origin and context checks; a .gov suffix alone is insufficient. Conflicting eligible
values remain unresolved. This policy comparison isolates the acceptance rule on
the same evidence; comparisons with older pilots change several components and
cannot isolate a single causal improvement.

## Interpretation and limitations

For this approved DOT task, the specialized public catalog plus structured API is
a useful additional retrieval service; Brave also found the necessary datasets.
Socrata is not a replacement for general web search outside supported catalogs.
The practical next step is to test new quarters, schemas and deliberately
conflicting sources before choosing a production workflow or subscription.

All observations share a quarter, dataset family and schema. Two query templates
produce highly repetitive searches; 24 held-out records are not 24 independent
new-source discovery problems. The study measures record recovery within this
known domain, not broad business-data generalization. Public records may also be
known to search indexes. The benchmark references come from DOT itself, so measured
accuracy is agreement with a frozen DOT reference, not independent verification
that the published fares are true. A trusted publisher can still make errors.
Zero incorrect acceptances here does not establish safety on unseen datasets.

Raw responses, hashes and source snapshots remain private under ignored `runs/`.
Frozen core files and saved snapshots matched after evaluation; all 510 saved
response-evidence hashes across the two structured runs were verified. The freeze
covers explicitly listed core files, not a complete operating-system or transitive
module environment; the imported input loader in `evaluate_business.py` is not
included in that core list. Request durations and run time windows are recorded,
but individual response wall-clock timestamps are not. These are reproducibility
limitations to address in a later version, not reasons to silently alter this run.

## Files and reproduction

- [Method, source policy and commands](week3-structured-retrieval.md)
- [Sanitized per-trial scores, metrics and frozen core hashes](week3-structured-results.json)
- `retrieve_record.py`: one-record entry point; `structured_retrieval.py`: discovery,
  structured extraction and verification; `evaluate_structured.py`: run/freeze/score.
- Local evidence folders: `runs/week3-structured-development-v2` and
  `runs/week3-structured-evaluation-v2`. These are not included in public Git commits.

Install `requirements-business.txt`, then run
`python retrieve_record.py --record-id airfare-01 --provider socrata` from the
repository. This makes live public API requests without an API key. Full paired
replication requires the existing SerpApi and Brave keys and fresh output folders;
see the method guide. Repeating these exposed observations is replication rather
than a new unseen evaluation.

This completes the retrieval/verification experiment and three-service comparison.
The comprehensive Week 3 research report still needs Jaideep's literature review
and sequential-decision formulation. Nothing in these results establishes that
research contribution yet.

Follow-up: the [Week 2 rejection audit](week3-rejection-audit.md) directly examines
the earlier PEP acceptance gap; the [technical task status](week3-technical-task-status.md)
separates completed experiments from remaining generalization research.
