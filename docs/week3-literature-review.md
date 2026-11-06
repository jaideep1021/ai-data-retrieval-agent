# Literature review and modeling corrections

Prepared 6 November 2026 from Jaideep's supplied review and primary-source checks.
This is a focused initial synthesis, not a systematic review or a novelty finding.
Paper identities and abstract-level relevance were checked; only the information
cost paper's relevant full-text discussion was additionally inspected. No claim
is made that all proofs or experiments have been independently reproduced.

## Relevant foundations

- Frazier, Powell and Dayanik (2008), A Knowledge-Gradient Policy for Sequential
  Information Collection. SIAM Journal on Control and Optimization 47(5), 2410–2439.
  https://doi.org/10.1137/070693424
  Studies myopic expected improvement in terminal selection value under a specific
  Bayesian ranking-and-selection model. It motivates one-step lookahead, not a
  general optimality guarantee for our web agent.
- Ni, Charoenphakdee, Honda and Sugiyama (2019), On the Calibration of Multiclass
  Classification with Rejection. NeurIPS 2019 camera-ready preprint.
  https://arxiv.org/abs/1901.10655
  Supports cost-sensitive prediction with rejection; theoretical surrogate-loss
  calibration should not be confused with empirical probability calibration.
- Li and Oliva (2020 preprint, revised 2021), Active Feature Acquisition with
  Generative Surrogate Models. https://arxiv.org/abs/2010.02433
  Models acquisition of missing features and estimates potential information gain.
  Web-source discovery adds unknown schemas, provenance and source dependence.
- Asai, Wu, Wang, Sil and Hajishirzi (2023 preprint), Self-RAG Learning to Retrieve,
  Generate, and Critique through Self-Reflection. https://arxiv.org/abs/2310.11511
  Demonstrates learned on-demand retrieval and reflection. It does not supply a
  calibrated business-value acceptance probability for our implementation.
- Mallen, Asai, Zhong, Das, Khashabi and Hajishirzi (2023), When Not to Trust
  Language Models Investigating Effectiveness of Parametric and Non-Parametric
  Memories. ACL. https://aclanthology.org/2023.acl-long.546/
  Finds retrieval helpful for less-popular factual knowledge; this is motivation
  for adaptive retrieval, not proof that popular facts need no verification.
- Li, Gao, Meng, Li, Su, Zhao, Fan and Han, A Survey on Truth Discovery
  (2015 preprint; 2016 ACM publication). https://arxiv.org/abs/1505.02463
  https://doi.org/10.1145/2897350.2897352
  Reviews joint estimation of source reliability and truth from conflicting data.
  The survey alone does not establish a particular sequential cost-aware policy.
- De Sabbata, Sumers, AlKhamissi, Bosselut and Griffiths, Rational Metareasoning
  for Large Language Models (2024 initial preprint, 2025 revision).
  https://arxiv.org/abs/2410.05563
  Studies selective intermediate reasoning and computation cost. It is related
  motivation, rather than a direct external-source acquisition model.
- Pomatto, Strack and Tamuz, The Cost of Information The Case of Constant
  Marginal Costs (2018 initial preprint, 2023 revision).
  https://arxiv.org/html/1812.04211v4
  Characterizes information costs under stated axioms using distinguishability
  between states. Do not replace observed API charges with a generic
  prior-to-posterior KL formula on the strength of this paper.
- Satsangi, Lim, Whiteson, Oliehoek and White (2020), Maximizing Information Gain
  in Partially Observable Environments via Prediction Reward. AAMAS.
  https://arxiv.org/abs/2005.04912
  Connects belief-based objectives with prediction rewards; uncertainty reduction
  is not automatically equal to improvement in our terminal decision utility.
- Zhu and Nowak (2022 initial preprint), Efficient Active Learning with Abstention.
  https://arxiv.org/abs/2204.00043
  Concerns label-efficient learning with abstention. Its guarantees do not transfer
  directly to inference-time retrieval of web evidence.

## Recent closely related preprints

Xu, Wu, Zeng, Paisley and Zhao (2026), Look Again Before You Abstain Budgeted
Conformal Evidence Acquisition for Reliable Vision-Language Model.
https://arxiv.org/abs/2606.16667
The abstract explicitly describes answer, abstain, or acquire additional visual
evidence. Its image-reinspection setting differs from paid web/API acquisition.
Do not claim its conformal guarantees for our policy without matching assumptions.

Geng (2026), Controlled Acquisition and Abstention in Three-Channel Score Conflicts.
https://arxiv.org/abs/2610.10808
Studies requesting an additional modality at a cost, with abstention. Its reported
comparisons depend on budget and reward definitions. This reinforces the need for
matched-budget baselines and sensitivity analysis, not a claim of universal gains.

These replace the supplied review's unidentified 2026 statement. Citation counts
are omitted. Information systems coverage currently consists mainly of data
management/truth-discovery work; dedicated IS journal coverage remains a search
gap. Classical SPRT is related background, not an exact accept/abstain model:
accepting an alternative hypothesis is different from declining a decision.

## Corrected decision formulation

Let x include the full candidate belief, evidence provenance/context, acquisition
history, remaining budget B and remaining horizon H. The hidden truth is v*;
source reliability may also be latent. For numerical fields define correctness
as |v - v*| <= epsilon using a tolerance declared before evaluation. Belief mass
outside discovered candidates must remain possible rather than being discarded.

Let p be the probability that the selected candidate is correct under that rule.
With correct utility U, incorrect loss E and abstention loss A, define
S(x) = max(p U - (1-p) E, -A).
At H=0, or without affordable actions, V(x)=S(x). Otherwise:
V(x) = max(S(x), max_k {-c_k + Expected[V(x_next) | x, k]}).
Available actions must respect both remaining budget and horizon. If costs are
random, their distributions and budget safeguards must be modeled explicitly.
Bayesian updates require specified likelihoods, including failed retrieval and
correlated sources; independent evidence updates are invalid for copied sources.

If stopping now, accept when p >= (E-A)/(U+E). This threshold follows from the
stated rewards, not from an LLM's self-reported confidence. One-step EVSI is
Expected[S(x_next)|x,k] - S(x); a myopic policy retrieves when its best net EVSI is
positive. This is an approximation: complementary future queries may have value
even when every one-step gain is nonpositive. Three contiguous confidence regions
are not guaranteed, and p alone generally is not a sufficient decision state.

An ordinary POMDP already permits state-dependent correctness rewards whose
belief expectation gives the expression above. A special belief-reward formalism
is not required unless introducing genuinely belief-dependent objectives.

## Candidate contribution and evidence gap

Investigate whether accounting for publisher provenance, reporting context and
source dependence improves cost-sensitive stopping relative to fixed retrieval
and confidence-only policies. This is a hypothesis requiring novelty review and
new experiments. The current code produces rules and evidence, not calibrated
posterior probabilities or learned likelihoods. Thirty related DOT records are
insufficient to establish general calibration. See the separate experiment plan.
