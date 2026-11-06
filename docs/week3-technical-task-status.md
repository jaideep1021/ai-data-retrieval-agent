# Week 3 technical task status and discussion guide

## 1. Test the approved DOT observations

Completed six development observations and a frozen 24-observation evaluation,
with each tested through three services (90 structured trials total). No expected
answers or source URLs were supplied to retrieval. The final path uses declared
DOT schema knowledge and automatic query templates, not Gemini planning.
Earlier LLM/PDF pilot failures are preserved separately.

| Held-out service | Correct candidates | Retrieved records | Correctly accepted | Mean seconds | Search allocation |
|---|---:|---:|---:|---:|---:|
| SerpApi | 0/24 | 0/24 | 0/24 | 2.89 | $1.20 |
| Brave | 24/24 | 24/24 | 24/24 | 8.98 | $0.12 |
| Socrata | 24/24 | 24/24 | 24/24 | 8.59 | $0 paid search |

Costs are scenarios, not invoices; public API requests are counted separately.
Challenges documented: period mismatch, airport versus city aggregation, rounded
PDF values, field definitions, duplicated sources and publisher provenance.
See [complete findings](week3-structured-findings.md).

## 2. Explain correct-but-rejected information

Completed an offline audit of the original 40 autonomous Week 2 trials. Thirteen
correct candidates were not accepted: twelve lacked a second usable grounded
source, and one triggered a title-prefix conflict. This directly explains the
observed acceptance gap without changing any historical scores.
See the [case-by-case audit](week3-rejection-audit.md).

## 3. Distinguish authoritative and secondary sources

Implemented for DOT: registered publisher hosts, official provenance, named
publisher attribution and matching origins, combined with period, market and
field checks. Unknown/secondary sources do not receive original-publisher trust
merely because they repeat a value. Conflicting eligible values block acceptance.
Identical records from different tables are not independent corroboration.

This is a configured DOT authority policy, not a general source-classification
system. A reusable policy should explicitly distinguish original publisher,
secondary citation, mirror and unknown provenance, retain the reason for that
classification, and test it against deliberately misleading examples. Those
broader classifications and their accuracy have not yet been demonstrated.
See [implemented rules and limitations](week3-structured-retrieval.md).

## 4. Integrate and compare an additional service

Socrata catalog/API integration and paired comparison are complete. The catalog
helps discover structured public datasets; it is not a general web search engine.
Brave and SerpApi used the same query templates and downstream adapter. SerpApi
returned search results, but the bounded path found an airport-pair table that
failed the city-market schema checks. The fallback query was too broad. Buying
more quota alone would not correct those workflow limitations.

These results compare workflows within a known domain. They do not rank services
universally. The 24 records share a quarter/schema and repeated discovery queries;
they are not 24 independent unfamiliar-dataset discovery problems.

## Ready for literature review; remaining research work

The requested technical experiments and rejection diagnosis are documented.
They establish a specialized baseline, not a universal adaptive agent. Nothing
has been pushed as part of this follow-up. The [combined three-page research report](week3-report.md) now incorporates
Jaideep's literature review with corrected modeling assumptions. The
[decision experiment](week3-decision-experiment-plan.md) remains proposed.

After reviewing that literature together, define a separate experiment in which
an agent chooses between accept, retrieve more, and unresolved. Candidate state
variables include source authority, context match, conflicting evidence, source
dependence, remaining budget and retrieval history. Measure correct acceptance,
incorrect acceptance, abstention, cost and latency. These are proposed design
inputs, not a completed model or a claim of research novelty.

Keep the current DOT workflow as a specialized comparator. Evaluate any adaptive
query/schema approach on fresh cases, without silently tuning against and reusing
this exposed benchmark as an unseen test. A SerpApi query-repair experiment is
useful follow-up work but does not need to delay the literature review.

## Short explanation for Dr. Sibdari

“We completed the DOT experiment and added Socrata as a third retrieval service.
Brave and Socrata recovered all 24 held-out records using a specialized structured
adapter. SerpApi's bounded search path did not locate an eligible dataset. We also
audited the earlier PEP results: twelve correct candidates lacked a second usable
source, and one was blocked by a title-prefix conflict. The new DOT policy can
accept a context-matching original-publisher record, but it is domain-specific.
We will use these results to motivate and evaluate a more adaptive, cost-aware
retrieval and stopping policy rather than claim a universal agent already exists.”
