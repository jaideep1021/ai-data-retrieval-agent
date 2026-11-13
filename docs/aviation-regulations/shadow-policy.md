# Trial-mode acceptance, review and unresolved routing

Implemented 9 November 2026. This is a rule-based, uncalibrated shadow policy.
It is not a learned cost-aware stopping policy and does not automatically publish
or verify events. No confidence probabilities or real-world accuracy are claimed.

## Outcomes

- WOULD_ACCEPT: passes the proposed conservative gates. In this trial phase the
  human still checks the recommendation, including possible missed errors.
- NEEDS_REVIEW: a potentially useful candidate has unresolved meaning, provenance,
  status, scope, date or evidence-coverage concerns. Targeted questions explain why.
- UNRESOLVED: no candidate, unsupported evidence, wrong country or mismatched topic.
  Do not accept it as written. It may need retrieval/correction or exclusion;
  this does not prove no regulatory event exists.

All outcomes retain verified=false, acceptance_applied=false and
human_validation_required=true. These fields describe shadow evaluation, not a
contradiction in routing. Later activation would require a separately reviewed
change; passing a synthetic test never enables real acceptance.

## Proposed gates for WOULD_ACCEPT

All cited evidence must pass the existing audit, and there must be no audit flags.
The full extracted text must fit the examined selection. The document must be
classified as a final instrument on a narrowly registered primary publisher host,
with explicit positive enactment wording, a supported announcement/effective date
within the study window, country in event evidence and international applicability.
Unknown optional dates remain unknown; one supported event date is required by
this initial policy to establish period membership. Earlier background and events
without an explicit full date therefore go to review rather than being rejected.

Draft, provisional, conditional or negated enactment language routes to review.
This intentionally strict initial gate can over-refer long documents and documents
that mention earlier drafts. Its language rules can also miss more subtle negation
or implications. A recognized host does not prove competence for every claim, and
an enactment phrase can appear in a quotation about a different instrument.
No automated cross-source conflict or source-independence analysis is added here.
These are reasons to validate shadow recommendations, not claim guaranteed safety.

## Functions and integration

aviation_triage.route_event consumes the candidate, current audit, selected text
coverage and task. It does not change the claim or its dates. route_empty handles
no-candidate cases. aviation_verification.extract_review now attaches triage to
new autonomous/replay output. triage_aviation.execute applies the same logic offline
to previously saved outputs, preserving them and recording source/implementation
hashes. The human-label CSV is blank by design.

```sh
python triage_aviation.py --source runs/aviation-verification-20261109 --task-id KEN-aviation_safety_changes --output runs/aviation-shadow-new
```

This command makes zero API calls. Saved source documents remain private local
inputs and are not shipped with the repository.

## Observed results

All three current section-selected Kenya candidates received NEEDS_REVIEW. All
three prefix comparison outputs also received NEEDS_REVIEW. They are six saved
outputs of three documents, not six independent cases. No real candidate received
WOULD_ACCEPT. The clear positive route was exercised only with synthetic test text.
The metadata cases need underlying instruments and date/scope clarification. The
long PDF needs status/scope review and examination of omitted sections; the prefix
version is also prevented from simulated acceptance despite calling the PDF final.

No human labels have been filled. We cannot estimate acceptance precision, false
acceptance, review savings or accuracy yet. The eventual evaluation should report
incorrect WOULD_ACCEPT cases / all WOULD_ACCEPT cases, proposed automatic coverage,
unresolved rate and review burden on a larger, independently reviewed sample.
If no cases would be accepted, acceptance precision is undefined, not 100%.
Human labels should record original errors separately from corrected dataset values.

Final offline suite at this change: 147 tests, 146 passed, one optional browser test
skipped. Seven new routing tests include acceptance in shadow only, fabricated
quotes, incomplete coverage, missing dates, drafts, negation and empty outputs.
No API calls, billing changes, purchases or GitHub pushes were made for this step.
