# Human Plan: Proof-Conditioned Lean Faithfulness Study

Last updated: 2026-07-22


## 1. Simple Goal

We want to learn whether a proof-conditioned Lean system actually follows the proof it is given.

For the same theorem, we will write two complete and correct informal proofs that use different mathematical strategies. We will hold the Lean theorem statement fixed, give the system proof A or proof B, and test whether its generated Lean proof changes strategy accordingly.

The coding agent can build and run the infrastructure described in [proof-conditioned-faithfulness-EXECPLAN.md](proof-conditioned-faithfulness-EXECPLAN.md). The source-discovery, extraction, Lean-statement, and review handoff for the 30 A/B pairs is defined in [proof-strategy-pair-JOINT-CURATION-PLAN.md](proof-strategy-pair-JOINT-CURATION-PLAN.md). Humans remain responsible for mathematical trust, benchmark labels, statistical commitments, spending approval, and paper claims.

The submission goal remains a NeurIPS 2026 workshop. The official NeurIPS organizer schedule suggests August 29, 2026 Anywhere on Earth for workshop contributed-paper deadlines, but each workshop chooses its own deadline and paper rules. A matching workshop and its actual call have not yet been confirmed.


## 2. Progress

- [x] 2026-07-22 — Research idea reviewed and primary fixed-theorem A/B question selected.
- [x] 2026-07-22 — Sixty design questions resolved; Questions 38 and 44 deliberately kept open for research.
- [x] 2026-07-22 — Closest related work, provisional models/toolchain, analysis options, and NeurIPS organizer schedule checked.
- [x] 2026-07-22 — Coding-agent ExecPlan and human plan drafted.
- [ ] YYYY-MM-DD — Specific workshop and actual contributed-paper deadline verified.
- [ ] YYYY-MM-DD — Server access and qualified annotator schedule confirmed.
- [ ] YYYY-MM-DD — Five theorem-pair pilot approved and run.
- [ ] YYYY-MM-DD — Statistical and agreement decisions frozen.
- [ ] YYYY-MM-DD — Pilot go/no-go decision recorded.
- [ ] YYYY-MM-DD — Core benchmark frozen and run, if approved.
- [ ] YYYY-MM-DD — Paper, reproducibility review, release review, and submission completed.


## 3. What Humans Must Personally Own

- [ ] Verify the exact workshop, deadline, scope, page limit, submission site, archival policy, anonymity policy, and attendance requirement.
- [ ] Give the coding agent access to the chosen server and explain its scheduler, storage, and secret-management rules.
- [ ] Approve every benchmark theorem, both informal proofs, both Lean reference proofs, strategy labels, essential-step labels, and paraphrases.
- [ ] Complete the independent annotation calibration and production reviews.
- [ ] Freeze the primary statistical comparison before viewing core results.
- [ ] Freeze the inter-annotator agreement measures and acceptable-quality rule.
- [ ] Approve the final model slate after server and API smoke tests.
- [ ] Approve any paid API batch before it starts; the provisional 500 USD limit is a ceiling, not preauthorization.
- [ ] Decide whether pilot evidence is strong enough to expand from five pairs to the 30-pair core.
- [ ] Approve any expansion from 30 toward 50 pairs using the frozen precision rule.
- [ ] Review the final claims against the actual evidence, including null or negative findings.
- [ ] Approve all public data, outputs, prompts, and code after license and privacy review.
- [ ] Submit the paper and complete any workshop-specific author or attendance actions.


## 4. Immediate 48-Hour Checklist

These tasks are on the critical path because the workshop window may be short.

- [ ] Owner: project lead — search the official NeurIPS 2026 workshop list and OpenReview for a workshop explicitly welcoming AI for mathematics, formal reasoning, theorem proving, trustworthy reasoning, or evaluation.
- [ ] Owner: project lead — record the chosen workshop URL and contributed-paper deadline in this file.
- [ ] Owner: project lead — email workshop organizers immediately if the call is ambiguous about fit, archival status, or whether a pilot benchmark paper is welcome.
- [ ] Owner: project lead — identify a fallback venue or non-archival workshop if no suitable NeurIPS call exists.
- [ ] Owner: project lead — grant server access or identify the person who can do so.
- [ ] Owner: server administrator — provide GPU types and counts, GPU memory, queue policy, storage quota, allowed containers, outbound-network policy, and secret mechanism.
- [ ] Owner: project lead — confirm the second qualified annotator and schedule two calibration sessions.
- [ ] Owner: project lead — identify a statistician or methods-savvy reviewer for Questions 38 and 44.
- [ ] Owner: project lead — reserve two short weekly decision meetings until submission.
- [ ] Owner: coding agent — proceed with configuration-driven scaffolding and environment discovery; do not wait for a local project path.


## 5. NeurIPS 2026 Workshop Sprint

This schedule assumes the workshop deadline is near the organizer-suggested August 29 date. Replace it with the real deadline as soon as the call is verified.

### July 22–24: remove uncertainty

- [ ] Confirm the venue and actual deadline.
- [ ] Confirm the server and annotator.
- [ ] Select five pilot theorem pairs or source candidates.
- [ ] Agree on the minimum publishable story: counterfactual A/B responsiveness under a fixed Lean theorem.
- [ ] Schedule the statistical and annotation-method reviews.

### July 22–31: build and validate the pilot

- [ ] Approve the pilot theorem statements and two strategies per theorem.
- [ ] Make all 10 pilot reference Lean proofs compile without prohibited trust shortcuts.
- [ ] Approve essential-step labels, strategy signatures, incompatible signatures, and paraphrases.
- [ ] Review the dependency/utilization fixtures.
- [ ] Run a cheap end-to-end smoke test before approving paid or long GPU runs.

### August 1–7: run pilot and freeze the method

- [ ] Complete annotator calibration on five separate calibration examples or relabel them after rubric freeze.
- [ ] Resolve Questions 38 and 44.
- [ ] Review pilot validity, classification errors, cost, runtime, and annotation burden.
- [ ] Freeze prompts, model revisions, analysis definitions, and ambiguity handling.
- [ ] Decide whether the paper is a five-pair pilot, a larger benchmark, or should move to the fallback venue.

### August 8–15: expand only if the pilot passes

- [ ] Grow the approved benchmark toward 15–30 pairs without weakening review.
- [ ] Run the frozen conditions on approved pairs.
- [ ] Complete blinded human review of disagreements, uncertain outputs, and the random audit.
- [ ] Begin the paper with methods and benchmark construction; do not wait for final numbers.

### August 16–22: finish core analysis

- [ ] Close missing run cells or document why they are missing.
- [ ] Complete adjudication and agreement analysis.
- [ ] Run theorem-clustered confidence intervals and prespecified sensitivity analyses.
- [ ] Write error analysis, limitations, related work, and reproducibility sections.
- [ ] Decide whether the corrupted/mismatched extension fits without delaying the core.

### August 23–actual deadline: paper and release

- [ ] Freeze figures and tables.
- [ ] Run code, data, license, and claim reviews.
- [ ] Reproduce the headline table from a clean environment.
- [ ] Conform to the actual workshop template, anonymity rule, and page limit.
- [ ] Prepare the permitted code/data release or an anonymized artifact.
- [ ] Submit early enough to handle upload or formatting failures.

### After submission

- [ ] Release permitted artifacts regardless of whether the main hypothesis was supported.
- [ ] Record reviewer questions and experiment deviations.
- [ ] Expand toward 50 theorem pairs only under the frozen precision rule and available resources.
- [ ] Consider the full theorem-plus-proof, repair, agentic/RAG, and human-auditability extensions.


## 6. Human Approval Gates

The coding agent should keep working on independent tasks while a gate is open. It may not cross a gate that changes the scientific contract.

### Gate H0 — venue fit

- [ ] A specific NeurIPS 2026 workshop call is linked here: ______________________________
- [ ] Actual contributed-paper deadline and time zone: ______________________________
- [ ] Page limit and template: ______________________________
- [ ] Archival or non-archival: ______________________________
- [ ] Anonymous or non-anonymous: ______________________________
- [ ] Attendance or registration requirement: ______________________________
- [ ] Organizers confirmed fit if the call was ambiguous.
- [ ] Fallback venue: ______________________________

Approval record:

- [ ] Approved by: __________________  Date: __________

If no suitable workshop exists, retain NeurIPS workshop as the desired goal in the project history but activate the fallback venue. Do not describe a nonexistent call in the paper.

### Gate H1 — server and secrets

- [ ] Server hostname or access method is documented outside the public repository.
- [ ] Scheduler/partition and job limits are known.
- [ ] GPU model, count, and memory are known.
- [ ] Storage quota and approved artifact location are known.
- [ ] Outbound network and model-download rules are known.
- [ ] API secrets will use environment variables or a secret manager.
- [ ] No secret value appears in configuration, logs, or this plan.
- [ ] The agent's environment report has been reviewed.

Approval record:

- [ ] Approved by: __________________  Date: __________

The server project path is intentionally not selected in advance. The coding agent must discover or receive it on the server and keep paths configurable.

### Gate H2 — pilot benchmark trust

For each of the five pilot theorem pairs:

- [ ] The exact Lean theorem matches the intended informal statement.
- [ ] Informal proof A is correct and sufficiently complete.
- [ ] Informal proof B is correct and sufficiently complete.
- [ ] A and B use mathematically different strategies, not merely different wording or tactic style.
- [ ] Reference Lean proof A compiles and realizes strategy A.
- [ ] Reference Lean proof B compiles and realizes strategy B.
- [ ] Both references pass prohibited-placeholder and axiom audits.
- [ ] Required and incompatible strategy signatures are clear.
- [ ] Acceptable alternative formal realizations are listed.
- [ ] Strategy-essential, logically necessary, and explanatory steps are separated.
- [ ] The dependency graph has no missing nodes, dangling edges, or cycles.
- [ ] Each paraphrase preserves the claims, dependency graph, and strategy.
- [ ] Source and contamination-risk metadata are recorded.
- [ ] Both annotators sign the item.

Approval record:

- [ ] All five pairs approved by annotator 1: __________________  Date: __________
- [ ] All five pairs approved by annotator 2: __________________  Date: __________

### Gate H3 — evaluation and statistics freeze

- [ ] Question 38 is resolved: the exact primary statistical contrast is written in plain language and a formula.
- [ ] The rule for pairing the three samples across A and B is frozen.
- [ ] Unresolved and mixed labels have a primary coding rule and lower/upper-bound sensitivity analysis.
- [ ] Question 44 is resolved: agreement statistics and the reliability action threshold are frozen.
- [ ] The random human-audit sample is drawn reproducibly.
- [ ] The methods reviewer confirms theorem-level clustering.
- [ ] The analysis file and rubric are versioned and hashed.
- [ ] Core results have not been inspected before this approval.

Approval record:

- [ ] Methods approved by: __________________  Date: __________

### Gate H4 — model and spending approval

- [ ] At least one open-weight anchor is fully reproducible on the server.
- [ ] At least one relevant proof-conditioned pipeline has passed a smoke test, or its integration failure is documented.
- [ ] Specialized theorem-only systems are labeled as theorem-only baselines.
- [ ] Exact model IDs, weight revisions, licenses, quantization, and decoding settings are recorded.
- [ ] Provider terms permit the intended analysis and release.
- [ ] Pilot request count, projected token use, API cost, and GPU-hours are reviewed.
- [ ] The batch is below the provisional 500 USD aggregate ceiling.
- [ ] The owner explicitly approves this particular paid batch.

Approval record:

- [ ] Approved batch/run manifest: ______________________________
- [ ] Approved maximum spend: __________________  Date: __________

### Gate H5 — pilot go/no-go

The pilot passes when:

- [ ] All reference proofs compile and pass trust checks.
- [ ] The end-to-end pipeline completes without hidden manual edits.
- [ ] A known faithful fixture and a known unfaithful fixture are classified correctly.
- [ ] Used and unused explicit local facts are distinguished.
- [ ] Annotators can apply the rubric consistently in reasonable time.
- [ ] Failures and unresolved cases remain visible rather than being dropped.
- [ ] Projected core runtime and cost fit the remaining schedule.
- [ ] Projected human review workload fits the remaining schedule.

Decision:

- [ ] Proceed to 30-pair core.
- [ ] Submit a rigorous five-pair pilot.
- [ ] Revise the pilot and rerun under a new version.
- [ ] Move to the fallback venue.

Chosen option, rationale, owner, and date: __________________________________________

### Gate H6 — core freeze and expansion

- [ ] The 30-pair benchmark is human approved before core inference.
- [ ] Prompts, signatures, model revisions, seeds, inclusion rules, and analysis are frozen.
- [ ] Any deviation from the pilot is declared exploratory or versioned.
- [ ] After 30 pairs, the main interval width is computed using the frozen method.
- [ ] Expansion toward 50 is triggered only if total interval width is greater than about 20 percentage points and budget, annotation, and deadline permit.
- [ ] Expansion is not based on whether the result looks favorable.

Approval record:

- [ ] Freeze manifest: __________________  Approved by: __________________  Date: __________

### Gate H7 — claims, release, and submission

- [ ] Every headline claim has a corresponding table, figure, or audited qualitative example.
- [ ] Validity, conditional responsiveness, and strict end-to-end responsiveness are not conflated.
- [ ] Conditional-on-validity estimates are labeled descriptive.
- [ ] Step utilization is not described as hidden model reasoning.
- [ ] Theorem samples, not model outputs, define the uncertainty unit.
- [ ] Null, mixed, and unresolved findings are reported.
- [ ] Model and dataset licenses have been checked.
- [ ] Public raw outputs are allowed by provider and source terms.
- [ ] The paper states all deviations from the frozen plan.
- [ ] The code/data artifact reproduces the reported aggregate numbers.
- [ ] The submission satisfies the workshop's exact rules.

Approval record:

- [ ] Scientific claims approved by: __________________  Date: __________
- [ ] Release approved by: __________________  Date: __________
- [ ] Submitted by: __________________  Date/time: __________


## 7. What “Annotator” Means

An annotator is a qualified human reviewer, not a software package and not the auxiliary language-model judge.

For this study, each annotator should be comfortable reading mathematical proofs and Lean 4 code. The person does not need to be the benchmark author, but should be able to decide whether:

- [ ] two informal proofs are mathematically correct;
- [ ] their strategies are genuinely different;
- [ ] a Lean proof realizes strategy A, strategy B, a mixture, or another strategy;
- [ ] an informal step appears formally, perhaps through several Lean steps or implicitly;
- [ ] an explicitly formalized intermediate result is actually used;
- [ ] a paraphrase preserves the original proof;
- [ ] a case is too ambiguous to resolve confidently.

The two annotators first label a five-theorem calibration set independently. They then discuss disagreements, revise the written rubric, and freeze it. Calibration labels do not count toward final agreement unless both people independently relabel the examples after the freeze.

During production annotation, each person works independently and is blinded to the model, prompt, sample number, expected A/B result, and the paired output from the other condition. Original labels are never erased. After independent work, disagreements are discussed to reach consensus. A case remains unresolved if consensus is not possible; a third expert is used only if the case could materially change the main conclusion.


## 8. Annotation Work Plan

### Prepare the rubric

- [ ] Define the hierarchical strategy taxonomy with examples.
- [ ] Give each theorem pair required signatures for A and B.
- [ ] Give each pair incompatible signatures for A and B.
- [ ] List acceptable formal refinements that should still count as a match.
- [ ] Define mixed_or_alternative and unresolved with examples.
- [ ] Define strategy-essential, logically necessary, and explanatory step roles.
- [ ] Define used, unused, implicit, and unresolved utilization states.
- [ ] Include one-to-many and many-to-one step-alignment examples.
- [ ] Include shortcut and automation-bypass examples.
- [ ] Freeze and version the rubric after calibration.

### Review benchmark inputs

- [ ] Annotator 1 reviews all theorem pairs independently.
- [ ] Annotator 2 reviews all theorem pairs independently.
- [ ] Each annotator checks the original proof before seeing the paraphrase.
- [ ] Paraphrase validation is blind to which text is original.
- [ ] Disagreements in pair validity or strategy distinctness block benchmark inclusion.

### Review generated outputs

- [ ] Automatic extraction and the auxiliary judge run first.
- [ ] Humans review every automatic-versus-judge disagreement.
- [ ] Humans review every uncertain or malformed case.
- [ ] Humans review a seeded random 25 percent of the remaining cases, with at least 10 when the pool is small.
- [ ] Each output is judged independently before its A/B counterpart is revealed.
- [ ] Original labels and comments remain stored after adjudication.
- [ ] Time per item is recorded to estimate the core workload.

### Annotation quality check

- [ ] Raw agreement is reported.
- [ ] The frozen chance-corrected and multi-label statistics are reported.
- [ ] Low-agreement label categories receive a written error analysis.
- [ ] Rubric changes after production begins create a new rubric version.
- [ ] Affected outputs are relabeled or explicitly marked incomparable.


## 9. Open Research Questions

These questions stay open until the named evidence is collected. Questions 38 and 44 are deliberately not auto-resolved by the coding agent.

### Q38 — What exactly is the primary statistical contrast?

Current recommendation: use strict end-to-end A/B responsiveness as the primary outcome. A paired result succeeds only when both generated proofs compile, the proof-A-conditioned output matches strategy A, and the proof-B-conditioned output matches strategy B. Report proof-reliance lift relative to theorem-only as a supporting contrast. Treat target match among valid outputs as descriptive because conditioning on validity can introduce selection.

- [ ] Decide how the three samples in proof A and proof B are paired.
- [ ] Decide whether the primary theorem score averages sample pairs, uses a fixed matched index, or treats any per-sample success differently.
- [ ] Confirm the exact formula for directional discrimination.
- [ ] Confirm the exact theorem-only comparison.
- [ ] Confirm conservative handling of mixed and unresolved labels.
- [ ] Run a small simulation showing the estimator and theorem-clustered interval behave sensibly at 30 theorem pairs.
- [ ] Obtain methods-review sign-off before inspecting core results.

Owner: __________________

Due: before Gate H3, preferably 2026-08-05

Evidence required: a one-page analysis specification, formulas, simulation output, and reviewer approval.

Status/decision: ________________________________________________________________

### Q44 — Which agreement measures and thresholds should we use?

Current recommendation: report raw agreement and Gwet's AC1 for binary target-match labels; Jaccard similarity plus label-wise precision/recall/F1 for multi-label strategies; edge F1 for proof dependency graphs; and nominal Krippendorff alpha for used/unused/implicit/unresolved utilization. Report Cohen's kappa only as a sensitivity statistic.

- [ ] Confirm each statistic matches the label type and missing-data pattern.
- [ ] Decide whether agreement is calculated before or after excluding malformed outputs.
- [ ] Define the minimum acceptable calibration quality and the action if it is not met.
- [ ] Avoid treating one universal threshold as proof that every category is reliable.
- [ ] Predefine a category-level error analysis when agreement is weak.
- [ ] Obtain methods-review sign-off.

Owner: __________________

Due: before Gate H3, preferably 2026-08-05

Evidence required: worked examples from the calibration labels and a short rationale linked to the frozen rubric.

Status/decision: ________________________________________________________________

### Venue and deadline

- [ ] Identify an actual NeurIPS 2026 workshop whose scope fits.
- [ ] Verify its contributed-paper deadline rather than relying only on the organizer suggestion.
- [ ] Verify whether the paper is archival and whether later conference submission is allowed.
- [ ] Verify page limit, anonymity, template, submission system, and attendance.
- [ ] Contact organizers if no AI-for-math/formal-reasoning workshop is yet publicly indexed.

Owner: __________________

Due: 2026-07-24

Status/decision: ________________________________________________________________

### Exact model slate

- [ ] Benchmark current frontier API models that can accept the preservation prompt.
- [ ] Find at least one reproducible open-weight general/code model that fits the server.
- [ ] Smoke-test candidate specialized Lean provers.
- [ ] Smoke-test ProofBridge and ProofFlow or document incompatibilities.
- [ ] Verify licenses and release restrictions.
- [ ] Freeze exact revisions and decoding after pilot evidence.

Owner: __________________

Due: before Gate H4

Status/decision: ________________________________________________________________

### Lean and Mathlib revision

- [ ] Start from Lean 4.15 because the closest released proof-conditioned systems use it.
- [ ] Compile all pilot references.
- [ ] Verify ProofBridge/ProofFlow compatibility.
- [ ] Pin the exact Mathlib tag and commit in the lockfile and manifest.
- [ ] Record any system that requires a separate environment.

Owner: coding agent proposes; project lead approves

Due: before pilot generation

Status/decision: ________________________________________________________________

### Dependency and utilization measurement

- [ ] Test used-constant extraction and explicit-binder use on controlled fixtures.
- [ ] Run safe deletion tests for used and unused local facts.
- [ ] Decide whether the normalized full dependency graph is reliable enough for the workshop.
- [ ] If not, freeze explicit local-step utilization as the workshop metric.
- [ ] State clearly that formal dependency is not hidden chain-of-thought.

Owner: coding agent proposes; both annotators review

Due: before Gate H5

Status/decision: ________________________________________________________________

### Benchmark source and contamination

- [ ] Search ProofNet, NaturalProofs, LeanDojo, educational texts, and newly authored examples for source material.
- [ ] Confirm no ready-made public set already contains intentional A/B complete strategy pairs for the exact task.
- [ ] Keep about two-thirds newly written or materially adapted.
- [ ] Record exact source, familiarity, adaptation, and likely training exposure.
- [ ] Decide whether any highly familiar theorem belongs only in a contamination analysis.

Owner: __________________

Due: before each pair reaches Gate H2/H6

Status/decision: ________________________________________________________________

### Paraphrase validity

- [ ] Decide whether an LLM may draft paraphrases.
- [ ] Require human editing regardless of drafting method.
- [ ] Blind the second annotator to original versus paraphrase.
- [ ] Confirm claims, strategy, and dependency edges remain unchanged.
- [ ] Record changes that go beyond wording and reject those paraphrases.

Owner: benchmark author plus annotator 2

Due: before pair freeze

Status/decision: ________________________________________________________________

### Corrupted and mismatched extension

- [ ] Select a stratified 10-theorem subset only after the core is safe.
- [ ] Define exactly one essential corruption per corrupted proof.
- [ ] Match irrelevant proofs on domain, length, and notation.
- [ ] Define the desired safe response for each case.
- [ ] Drop or postpone this extension if it threatens the primary submission.

Owner: __________________

Due: Gate H5 scope decision

Status/decision: ________________________________________________________________

### Full theorem-plus-proof track

- [ ] Decide whether to let models generate the formal theorem as well as its proof.
- [ ] Keep all such results separate from the fixed-theorem primary analysis.
- [ ] Define semantic theorem-equivalence checking if the track proceeds.
- [ ] Postpone if it threatens the fixed-theorem experiment.

Owner: project lead

Due: after pilot gate

Status/decision: ________________________________________________________________


## 10. Accepted Experimental Design

This section records decisions that should not be reopened casually.

- [x] The paper is an evaluation/benchmark paper, not a model-training paper.
- [x] Counterfactual strategy responsiveness is the primary claim.
- [x] Step traceability is a secondary explanatory analysis.
- [x] The primary track uses a trusted fixed Lean theorem; full autoformalization is secondary.
- [x] Each pair has two complete, correct, genuinely different proof strategies.
- [x] Validity, conditional responsiveness, and strict end-to-end responsiveness are separate.
- [x] Pilot size is five pairs; core begins at 30; precision may justify expansion toward 50.
- [x] Approximately two-thirds of pairs are new or materially adapted.
- [x] Version-one domains are elementary arithmetic, finite sums/sets, algebra, divisibility, and inequalities.
- [x] Strategy labels are hierarchical and theorem-specific signatures are preregistered.
- [x] The core conditions are theorem-only, A, B, paraphrase A, and paraphrase B.
- [x] Preservation and validity-only prompt styles are compared.
- [x] Three outputs are retained per supported condition and prompt.
- [x] First attempt is primary; repair has at most two compiler-feedback rounds and is reported separately.
- [x] A 10-theorem corrupted/mismatched extension is optional and cannot delay the core.
- [x] Matching uses required signatures, incompatible signatures, and acceptable formal refinements.
- [x] Automatic evidence, an auxiliary language-model judge, and blinded human review are combined.
- [x] Human review covers all disagreements/uncertain cases plus a random 25 percent audit.
- [x] Step alignment may be one-to-many, many-to-one, or implicit.
- [x] Utilization states are used, unused, implicit, and unresolved.
- [x] Strategy-essential steps drive the main coverage analysis.
- [x] Benchmark records use versioned JSONL; derived analysis may use Parquet.
- [x] All reference proofs compile under a pinned environment with no prohibited placeholders.
- [x] Paraphrases are human edited and independently validated.
- [x] Core model calls have no retrieval, web search, or tools unless reported as a separate track.
- [x] At least one open-weight anchor must be fully reproducible.
- [x] Invalid content is not retried or replaced; transport failures may be retried.
- [x] A provisional 500 USD API ceiling requires explicit batch approval.
- [x] Generated proofs run in fresh processes with provisional 120-second and 4 GB limits.
- [x] The extractor may remove fences but may not repair or choose a best proof.
- [x] The theorem is the independent statistical unit.
- [x] Whole theorems are resampled for bootstrap intervals.
- [x] Unresolved cases remain in the analysis through conservative coding and bounds.
- [x] Evaluators are blinded to model, prompt, sample, and paired outputs.
- [x] Two qualified annotators calibrate, label independently, and preserve original judgments.
- [x] No human auditability/IRB study is required for the workshop minimum.
- [x] The project runs on a server with configuration-driven paths.
- [x] Credentials use environment variables or a server secret manager only.
- [x] The agent owns infrastructure; humans own trusted pairs, labels, spending, and claims.
- [x] The release proceeds regardless of whether the hypothesis is supported.
- [x] NeurIPS 2026 workshop remains the submission goal.


## 11. Human Workload and Roles

Assign names before pilot annotation.

Project lead: __________________

Responsibilities:

- [ ] venue and submission;
- [ ] final scientific scope;
- [ ] paid-run approvals;
- [ ] gate decisions;
- [ ] claim and release approval.

Benchmark author/Lean expert: __________________

Responsibilities:

- [ ] theorem selection and formal statements;
- [ ] proof A/B drafting;
- [ ] reference Lean proofs;
- [ ] signatures and step graphs;
- [ ] source and contamination notes.

Annotator 1: __________________

Responsibilities:

- [ ] calibration;
- [ ] independent pair validation;
- [ ] independent generated-proof review;
- [ ] adjudication discussion.

Annotator 2: __________________

Responsibilities:

- [ ] blind paraphrase and pair validation;
- [ ] calibration;
- [ ] independent generated-proof review;
- [ ] adjudication discussion.

Methods reviewer/statistician: __________________

Responsibilities:

- [ ] resolve Question 38;
- [ ] resolve Question 44;
- [ ] review clustering, uncertainty, ambiguity, and expansion rule;
- [ ] review final statistical language.

Server administrator, if separate: __________________

Responsibilities:

- [ ] access, quotas, scheduler, containers, networking, and secrets;
- [ ] help diagnose infrastructure failures without changing experiment semantics.

Coding agent:

- [ ] implement, test, document, and run the pipeline defined in the ExecPlan;
- [ ] surface missing human decisions as gates;
- [ ] keep raw artifacts immutable;
- [ ] produce auditable reports;
- [ ] never certify its own drafted benchmark pair as trusted.


## 12. Paper Checklist

### Main message

- [ ] State the question in one sentence: does changing a supplied correct proof change the generated Lean strategy while the theorem stays fixed?
- [ ] Explain why compilation accuracy alone cannot answer this.
- [ ] Present the paired benchmark and counterfactual evaluation as the main contribution.
- [ ] Distinguish mathematical strategy from superficial tactic style.

### Required results

- [ ] Validity by model and condition.
- [ ] Strict end-to-end A/B responsiveness with theorem-level intervals.
- [ ] Target match conditional on validity, labeled descriptive.
- [ ] Proof-reliance lift over theorem-only.
- [ ] Preservation-versus-validity-only prompt comparison.
- [ ] Original-versus-paraphrase comparison.
- [ ] Strategy-essential coverage and explicit utilization.
- [ ] Mixed, unresolved, shortcut, and bypass error analysis.
- [ ] Cost, runtime, and missing-cell accounting.
- [ ] First-attempt results separate from repair.

### Required limitations

- [ ] Small theorem count and domain coverage.
- [ ] Human judgment in defining and classifying strategy.
- [ ] Possible benchmark contamination.
- [ ] Model and provider version dependence.
- [ ] Conditional-on-validity selection.
- [ ] Lean proof terms do not reveal hidden model reasoning.
- [ ] Signature extraction may miss semantically equivalent strategies.
- [ ] Full theorem autoformalization and human auditability are outside the workshop minimum.

### Reproducibility

- [ ] Exact Lean and Mathlib revisions.
- [ ] Exact model revisions and dates.
- [ ] Prompt and chat-template hashes.
- [ ] Complete run manifests and request IDs.
- [ ] Benchmark schema and annotation rubric.
- [ ] Confidence-interval code and analysis seed.
- [ ] License-aware artifact release.
- [ ] Clean reproduction of headline numbers.


## 13. Decision Log

- [x] 2026-07-22 — Keep NeurIPS 2026 workshop as the submission goal.
- [x] 2026-07-22 — Use separate coding-agent and human plans.
- [x] 2026-07-22 — Leave the server project path open until server discovery.
- [x] 2026-07-22 — Keep Question 38 open for research and methods review.
- [x] 2026-07-22 — Keep Question 44 open for research and methods review.
- [x] 2026-07-22 — Treat the annotator as a qualified human Lean/math reviewer.
- [x] 2026-07-22 — Accept all other interview recommendations summarized in Section 10.
- [ ] YYYY-MM-DD — Record the chosen workshop and actual deadline.
- [ ] YYYY-MM-DD — Record the final Q38 decision.
- [ ] YYYY-MM-DD — Record the final Q44 decision.
- [ ] YYYY-MM-DD — Record the server and frozen toolchain.
- [ ] YYYY-MM-DD — Record the pilot gate decision.
- [ ] YYYY-MM-DD — Record the core freeze and final model slate.
- [ ] YYYY-MM-DD — Record the submission and artifact-release outcome.


## 14. Current Status and Next Concrete Action

Planning and related-work verification are complete. No experiment implementation or trusted benchmark pair has yet been produced in this workspace.

The next human action is to complete the Immediate 48-Hour Checklist, beginning with the exact NeurIPS 2026 workshop call and server access. The coding agent can begin Milestone 0 and the reproducible scaffold immediately after it is handed this directory and a server-access context.

Official NeurIPS workshop schedule: https://neurips.cc/Conferences/2026/CallForWorkshops

Coding plan: [proof-conditioned-faithfulness-EXECPLAN.md](proof-conditioned-faithfulness-EXECPLAN.md)
