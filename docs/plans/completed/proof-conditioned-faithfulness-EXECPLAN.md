> **SUPERSEDED (2026-07-24).** This plan is retired (todo T009). The single
> controlling plan is [../active/PLAN.md](../active/PLAN.md). This file is kept as
> historical reference only — do not execute from it.

# ExecPlan: Counterfactual Faithfulness in Proof-Conditioned Lean Autoformalization

This is a living implementation plan. The coding agent must keep the Progress, Surprises & Discoveries, Decision Log, and Outcomes & Retrospective sections current while carrying out the work. Every entry added to those sections must include a date. The project is complete only when the observable acceptance criteria in this plan pass; creating files without running the checks is not completion.


## Purpose and Research Outcome

Build and run a reproducible benchmark that asks a sharper question than ordinary Lean proof success: when a model receives one of two different, complete, correct informal proofs of the same fixed theorem, does the generated Lean proof follow the supplied proof's mathematical strategy?

The primary experiment holds the trusted Lean theorem statement fixed. For each theorem, humans curate two correct informal proofs, A and B, that reach the same conclusion through genuinely different mathematical strategies. A system receives the theorem alone, proof A, proof B, or a meaning-preserving paraphrase of A or B. The benchmark separately measures:

1. whether the generated Lean proof compiles;
2. whether it matches the strategy it was conditioned on;
3. whether it formalizes the strategy-essential steps in that proof;
4. whether those formalized steps are actually used in the final proof term; and
5. whether changing only the supplied proof from A to B changes the generated strategy in the corresponding direction.

The main artifact is an evaluation framework and paired benchmark, not a newly trained model. A secondary track may evaluate end-to-end theorem-plus-proof autoformalization, but it must not blur the primary fixed-theorem causal comparison.

A successful implementation lets a researcher run one command sequence on a server, resume interrupted model calls safely, validate every result in a pinned Lean environment, collect blinded human annotations, compute theorem-clustered uncertainty intervals, and rebuild all paper tables from immutable run artifacts.

The submission goal is a NeurIPS 2026 workshop. The official NeurIPS workshop organizer schedule suggests August 29, 2026 Anywhere on Earth for contributed-paper deadlines, but each workshop defines its own deadline, page limit, and archival policy. The coding schedule therefore begins with an urgent venue verification gate and supports a defensible five-pair pilot paper if a 30-pair benchmark cannot be completed without lowering scientific quality.


## Progress

- [x] 2026-07-22: Read the original research proposal and repository planning/code-quality instructions.
- [x] 2026-07-22: Complete a 60-question design interview and record accepted decisions.
- [x] 2026-07-22: Verify the closest related systems, candidate Lean mechanisms, model families, statistical options, agreement measures, and NeurIPS 2026 workshop timing.
- [ ] YYYY-MM-DD: Verify a specific NeurIPS 2026 workshop call, deadline, page limit, archival status, and scope; record the URL and decision in the Human Plan.
- [ ] YYYY-MM-DD: Discover and record the target server environment without assuming a local project path.
- [ ] YYYY-MM-DD: Resolve the open statistical estimands and agreement metrics with a qualified reviewer.
- [ ] YYYY-MM-DD: Scaffold the Python and Lean project, pin all dependencies, and make the clean-room checks pass.
- [ ] YYYY-MM-DD: Implement and test the benchmark schema, validation, immutable artifact store, deterministic request IDs, and resumable run manifests.
- [ ] YYYY-MM-DD: Implement the isolated Lean checker, exact-statement guard, prohibited-placeholder audit, axiom audit, resource limits, and diagnostics.
- [ ] YYYY-MM-DD: Compile and human-approve all five pilot theorem pairs and their two reference Lean proofs.
- [ ] YYYY-MM-DD: Prototype direct proof-dependency and explicit local-step-utilization extraction on controlled fixtures.
- [ ] YYYY-MM-DD: Implement model adapters, prompt rendering, deterministic extraction, caching, transport retries, and cost accounting.
- [ ] YYYY-MM-DD: Implement blinded annotation bundles, automatic strategy signatures, auxiliary LLM judging, human adjudication, and agreement reports.
- [ ] YYYY-MM-DD: Implement theorem-level metrics, conservative ambiguity bounds, clustered bootstrap intervals, and secondary mixed-effects models.
- [ ] YYYY-MM-DD: Run the five-pair pilot across the frozen condition matrix and pass the pilot gate.
- [ ] YYYY-MM-DD: Freeze benchmark rules, prompts, model revisions, analysis choices, and a preregistration-style manifest before core runs.
- [ ] YYYY-MM-DD: Run the 30-pair core benchmark or invoke the preregistered precision-based expansion rule toward 50 pairs.
- [ ] YYYY-MM-DD: Run the stratified 10-theorem mismatched/corrupted-proof extension if it does not threaten the core deadline.
- [ ] YYYY-MM-DD: Build all tables, figures, error analyses, release manifests, and paper-ready method text from versioned artifacts.
- [ ] YYYY-MM-DD: Perform independent code, data, claim, license, and reproducibility reviews.
- [ ] YYYY-MM-DD: Reproduce the accepted result from a fresh clone or clean server allocation using the documented commands.


## Surprises & Discoveries

- 2026-07-22: The repository's .agent/AGENT.md points to .agent/PLANS.md, but the available specification is .agent/PLAN.md. This ExecPlan follows .agent/PLAN.md.
  Evidence: the former path is named in .agent/AGENT.md, while only .agent/PLAN.md exists in the current tree.
- 2026-07-22: The closest verified systems evaluate end-to-end formalization, graph-guided formalization, sentence-level verification, or robustness to edits. None of the verified work directly compares two complete, correct, strategy-distinct proofs for the same fixed Lean theorem.
  Evidence: the verified tasks and published evaluation units are summarized with primary links in Related Work and Positioning.
- 2026-07-22: ProofBridge and ProofFlow both use Lean 4.15, making Lean 4.15 the provisional interoperability choice rather than an arbitrary newest version.
  Evidence: both released repositories and papers document Lean 4.15 environments.
- 2026-07-22: Lean exposes used-constant and axiom-analysis utilities, but a full normalized dependency graph for tactic-generated proof terms is not guaranteed to preserve the source-level explanation. The workshop-minimum metric is therefore explicit-step utilization, with the complete graph treated as an extension.
  Evidence: Lean documents used-constant collection and axiom auditing, while the controlled deletion prototype in Milestone 4 is still required to validate the project-specific interpretation.
- 2026-07-22: The official NeurIPS 2026 workshop schedule leaves only about five weeks from this plan's date to the suggested contributed-paper deadline, while no matching workshop call has yet been verified. Venue discovery is an immediate human gate.
  Evidence: the official organizer call suggests August 29, 2026 Anywhere on Earth, but delegates actual paper rules to each selected workshop.
- 2026-07-22: The current planning workspace is not a Git repository.
  Evidence: git status exits with “not a git repository,” and no .git directory exists under the workspace root. The server scaffold must therefore be created in or connected to an actual repository before implementation commits begin.


## Decision Log

Unless a later entry says otherwise, the decision owner is the user and the recording author is Codex; each entry's leading date is its decision date.

- 2026-07-22: Treat counterfactual strategy responsiveness as the primary claim and step traceability as a secondary explanatory analysis.
  Rationale: holding the theorem fixed and changing only the proof provides the cleanest evidence that a system uses proof content.
- 2026-07-22: Separate compilation validity, responsiveness conditional on validity, and strict end-to-end responsiveness.
  Rationale: a model should not receive a high faithfulness score for non-compiling outputs, while failure sources must remain diagnosable.
- 2026-07-22: Use a five-pair pilot, a 30-pair core, and a preregistered precision rule that may expand toward 50.
  Rationale: this is feasible under the workshop schedule while preserving a principled path to narrower uncertainty.
- 2026-07-22: Use theorem-only, proof A, proof B, paraphrase A, and paraphrase B conditions; compare a preservation prompt with a validity-only prompt; request three independent samples per supported cell.
  Rationale: this symmetric design tests proof use, prompt sensitivity, and surface-form robustness.
- 2026-07-22: Require two valid, compiling, human-approved Lean reference proofs and preregistered strategy signatures for every benchmark pair.
  Rationale: the benchmark intervention must reflect mathematical strategy rather than style.
- 2026-07-22: Use automatic extraction plus a blinded auxiliary LLM judge, with humans reviewing all disagreements and uncertain cases plus a random 25 percent audit.
  Rationale: this balances scale with defensible expert control; the LLM is not the final authority.
- 2026-07-22: Use first-attempt results for the core claim. Report a separate repair track with at most two compiler-feedback rounds.
  Rationale: repair can improve validity but changes the interaction being measured.
- 2026-07-22: Keep all raw model outputs and failed attempts immutable. Allow transport retries, but never best-of selection or semantic cleanup.
  Rationale: resume behavior must not alter the sampling protocol.
- 2026-07-22: Reject sorry, admit, sorryAx, custom axioms, unsafe trust bypasses, native trust shortcuts, and changes to the theorem statement. Permit standard Mathlib classical axioms when disclosed by #print axioms.
  Rationale: successful elaboration alone is not sufficient evidence of a trusted proof.
- 2026-07-22: Use Python 3.12, uv, Pydantic plus JSON Schema, Typer, pytest, Ruff, Pyright, Lean 4, and Mathlib. Do not add a workflow framework until actual execution complexity requires one.
  Rationale: the stack is typed, testable, and small enough for a workshop project.
- 2026-07-22: Run on a server whose path and resources are discovered at execution time. Keep paths configuration-driven.
  Rationale: the user explicitly deferred local path selection.
- 2026-07-22: Retain NeurIPS 2026 workshop submission as the target, with a five-pair pilot fallback rather than inventing unreviewed benchmark items to meet a deadline.
  Rationale: deadline pressure may reduce scope, not evidence quality.


## Outcomes & Retrospective

No implementation outcome exists yet. At completion, replace this paragraph with the date, final benchmark size, model slate, Lean and Mathlib revisions, run-manifest IDs, primary estimates and confidence intervals, deviations from this plan, failed approaches, release location, and lessons for the next version. State clearly whether the primary claim was supported, contradicted, or inconclusive; a null result is a valid result.


## Repository Context and Starting Point

The current workspace contains planning and research-standard documents but no Lean project, evaluation implementation, or Git repository. The implementation agent must create or clone a Git repository under the server-side path selected during environment discovery, then copy or preserve these plans at its root. Do not run git init inside an unrelated server directory. The workspace-level deliverables are:

    proof-conditioned-faithfulness-EXECPLAN.md
    proof-conditioned-faithfulness-HUMAN_PLAN.md
    proof-strategy-pair-JOINT-CURATION-PLAN.md
    RESEARCH_CODE_STANDARD.md
    big-tech-code-review-standards.md
    .agent/AGENT.md
    .agent/PLAN.md

The agent must read all three planning documents and RESEARCH_CODE_STANDARD.md before coding. The joint curation plan is the authoritative workflow for agent source discovery, machine-processable extraction, Lean-statement drafting, and human promotion of the 30 A/B candidate pairs. Raw source data and model responses are immutable. Experimental prototypes may begin under experiments, but any code used for paper numbers must be promoted into the typed source package with tests, boundary checks, and documentation.

Use the following target structure. If the server repository already has a compatible layout, adapt names minimally and record the mapping in the Decision Log rather than duplicating infrastructure.

    .env.example
    .gitignore
    README.md
    pyproject.toml
    uv.lock
    lean-toolchain
    lakefile.toml
    lake-manifest.json
    ProofFaithfulness.lean
    ProofFaithfulness/
      Audit.lean
      Dependency.lean
      Reference/Pilot/
      Reference/Core/
    configs/
      experiment/pilot.yaml
      experiment/core.yaml
      models/
    data/
      raw/
      benchmark/pilot.jsonl
      benchmark/core.jsonl
      annotations/calibration.jsonl
      annotations/round1.jsonl
      annotations/adjudicated.jsonl
    schemas/
      benchmark.schema.json
      annotation.schema.json
      run-manifest.schema.json
    prompts/
      theorem_only_v1.txt
      preservation_v1.txt
      validity_only_v1.txt
      repair_v1.txt
    experiments/
      dependency_probe/
    src/proof_faithfulness/
      cli.py
      config.py
      ids.py
      schema.py
      artifacts.py
      models/
      generation/
      lean/
      evaluation/
      reporting/
    tests/
      unit/
      integration/
      fixtures/
    outputs/

The outputs directory, local caches, secrets, generated Lean candidate files, and raw licensed model responses are gitignored. Small schemas, benchmark metadata, human-authored proof texts, approved reference proofs, prompts, configurations, and aggregate tables are versioned when their licenses allow it.


## Terminology for a New Contributor

Lean 4 is the proof assistant that mechanically checks whether a formal proof establishes its stated theorem. Mathlib is Lean's community mathematical library. A tactic is a Lean command that transforms the current proof goal; after elaboration, Lean turns tactics and terms into a checked proof term. Compilation or validity in this plan means that Lean accepts the exact intended theorem in the pinned environment and the trust audit passes.

An informal proof is the human-readable mathematical argument. A reference Lean proof is a human-approved formal realization used to demonstrate that an intended strategy can be expressed in Lean; it is not a target string that generated outputs must copy. Strategy means the mathematical route, such as induction versus a closed-form algebraic derivation. A strategy signature is observable evidence expected from a route, such as induction cases, a characteristic intermediate lemma, or a particular decomposition. An incompatible signature is evidence that points to the competing route.

A condition is one cell of the experiment, such as theorem-only or proof-A-with-preservation-prompt. Counterfactual responsiveness means that the output changes in the expected direction when the supplied proof changes while the theorem and other factors remain fixed. Conditional responsiveness is measured only among outputs that compile. Strict end-to-end responsiveness counts invalid output as failure.

Step coverage asks whether strategy-essential informal claims appear in the formal proof. Utilization asks whether an introduced formal fact contributes to the final proof rather than merely appearing decoratively. A dependency graph represents proof steps as nodes and prerequisite relations as directed edges.

JSONL is a text format with one JSON object per line and is used for auditable records. Parquet is a typed columnar format used only for derived analysis tables. Pydantic validates Python data models and emits JSON Schema, which is a machine-readable description of allowed JSON. Typer provides the command-line interface. uv installs and locks the Python environment. Pyright checks Python types. Ruff formats and lints Python.

A model adapter is a small translation layer between the experiment's canonical request and a provider or local inference engine. vLLM is one possible local model server that exposes an OpenAI-compatible request format. A run manifest is the immutable inventory of configuration, requests, code revisions, and environment metadata for one experiment. A request ID is a hash-derived stable name for one exact generation attempt.

A clustered bootstrap estimates uncertainty by repeatedly resampling whole theorems, keeping every repeated condition for a theorem together. A mixed-effects logistic model is a secondary regression that accounts for repeated binary outcomes within a theorem through a theorem-specific random effect. These tools do not turn repeated model samples into additional independent theorems.


## Research Code Quality Rules

All code begins under the repository's exploratory tier, but any code reused by a second experiment or used to compute a paper number must be promoted into src/proof_faithfulness before that number is trusted. Promotion means adding typed public interfaces, Google-style contract docstrings, seeded tests with hand-checked or golden values, boundary assertions, Ruff compliance, and a passing Pyright basic check.

Every experiment script or notebook begins with a short purpose and date, and records its seed, complete configuration, benchmark version, toolchain revision, and parent run ID. A notebook result is not trusted until restart-and-run-all succeeds. Raw ingested data remains read-only; transformations write to derived data or outputs.

Metric, sampler, and transform code receives deterministic unit tests. Data pipelines receive schema and invariant tests on tiny fixtures. Assert theorem IDs, row counts, label domains, missingness rules, join cardinalities, and condition alignment at input and output boundaries so a silent mismatch fails early.

Every library-tier change receives an independent review before it contributes to a reported result. Fix known problems before merge or place them in a dated tracked issue; do not leave unowned TODO comments. Use small commits whose messages explain why a scientific or engineering choice changed.


## Scientific Contract

### Unit, intervention, and claims

The theorem pair is the independent analysis unit. Samples, prompt variants, paraphrases, and conditions are repeated observations nested within a theorem; they are not independent theorem samples.

For theorem i, the intervention changes the supplied informal proof while holding these elements fixed:

1. exact Lean theorem declaration and imported environment;
2. model revision and decoding settings;
3. system prompt and output format, except for the preregistered preservation-versus-validity prompt comparison;
4. sample index or paired seed when the provider supports deterministic seeds;
5. resource limits and compiler environment; and
6. all benchmark metadata not explicitly manipulated.

The primary claim is narrow: changing the supplied correct proof from strategy A to strategy B changes the generated valid Lean proof toward the corresponding strategy more often than expected from theorem-only behavior.

Do not claim that proof conditioning caused human-like reasoning, that every essential informal step is logically necessary, or that proof-term dependencies fully recover model reasoning. Step alignment and utilization support a traceability analysis, not access to hidden cognition.

### Benchmark inclusion

Each core item contains one theorem and exactly two primary proof variants. A pair enters the benchmark only after:

1. the exact Lean theorem statement compiles in the pinned environment;
2. both human-authored reference Lean proofs compile with no prohibited placeholders or custom axioms;
3. both informal proofs are mathematically correct and complete enough to formalize;
4. the proofs use distinguishable mathematical strategies, confirmed by two qualified annotators who judge them without seeing the A/B names;
5. each strategy has required signatures, incompatible signatures, and allowed formal refinements recorded before model evaluation;
6. strategy-essential, logically necessary, and explanatory steps are labeled separately;
7. the proof dependency graph and paraphrase have been independently checked; and
8. source, adaptation, familiarity, and contamination-risk metadata are recorded.

Target composition is approximately two-thirds newly written or materially adapted pairs and one-third familiar educational examples. Core domains are elementary natural-number and integer reasoning, finite sums and finite sets, elementary algebra, divisibility, and inequalities. Avoid advanced analysis and geometry in version one because formalization overhead could dominate the faithfulness question.

The pilot has five pairs covering multiple domains and proof structures. The core begins with 30 pairs. Expansion toward 50 is allowed only if the total width of the main responsiveness interval is greater than roughly 20 percentage points after 30 pairs and annotation, cost, and deadline constraints permit it. The rule and exact statistic must be frozen before inspecting favorable or unfavorable model comparisons.

### Conditions and sampling

The core condition matrix is symmetric:

| Condition | Informal statement | Informal proof | Prompt style | Samples |
|---|---|---|---|---|
| theorem_only | yes | none | theorem-only validity | 3 |
| proof_a | yes | original A | preservation | 3 |
| proof_b | yes | original B | preservation | 3 |
| paraphrase_a | yes | paraphrased A | preservation | 3 |
| paraphrase_b | yes | paraphrased B | preservation | 3 |
| proof_a_validity | yes | original A | validity-only | 3 |
| proof_b_validity | yes | original B | validity-only | 3 |
| paraphrase_a_validity | yes | paraphrased A | validity-only | 3 |
| paraphrase_b_validity | yes | paraphrased B | validity-only | 3 |

Systems that cannot accept an informal proof run only in theorem_only and are labeled theorem-proving baselines, not proof-conditioned systems. Proof-conditioned pipelines may use their documented components, but core runs may not use theorem search, retrieval, web access, or interactive tools unless the same capability is deliberately defined as a separate agentic/RAG track.

Request order is randomized within each theorem and recorded. Use identical generation settings within a model wherever the API permits. Begin the pilot with temperature 0.2, top_p 1.0, and maximum output 8192 tokens, but do not silently override a specialized model's documented decoding recipe. Freeze and report every deviation. Three outputs mean three retained attempts, never best-of-three.

The first-attempt track is primary. The repair track can return the exact compiler diagnostic to the model for at most two rounds, stores every version, and reports results separately. Transport timeouts and rate-limit failures may be retried against the same deterministic request ID; invalid semantic output may not.

The robustness extension uses a stratified 10-theorem subset. A corrupted proof changes exactly one essential mathematical step in a subtle but unambiguous way. A mismatched proof comes from the same broad domain and has similar length and notation but does not prove the supplied theorem. Every extension item records the desired safe response, such as rejecting an invalid premise rather than blindly formalizing it.


## Data Contracts

### Benchmark record

Implement versioned Pydantic models and emitted JSON Schemas. A BenchmarkRecord contains:

    schema_version: str
    theorem_id: str
    domain: str
    difficulty: str
    source: SourceMetadata
    contamination: ContaminationMetadata
    informal_statement: str
    lean: LeanTheoremSpec
    proof_variants: tuple[ProofVariant, ProofVariant]
    split: Literal["pilot", "core", "extension"]
    status: Literal["draft", "human_approved", "frozen"]

LeanTheoremSpec contains the declaration name, exact declaration text, normalized statement hash, allowed imports, reference file paths, Lean version, Mathlib tag and commit, and expected allowed axioms.

Each ProofVariant contains proof_id, informal proof, one human-edited paraphrase, hierarchical strategy labels, required strategy signatures, incompatible signatures, acceptable formal refinements, an ordered list of proof steps, a dependency edge list, a compiling reference Lean file, annotator approvals, and optional corruption metadata. Each ProofStep contains a stable step_id, text, one or more roles from strategy_essential, logically_necessary, and explanatory, and zero or more predecessor step IDs.

Reject records with duplicate IDs, dangling edges, cycles, fewer or more than two primary variants, missing statement hashes, unapproved references in a frozen split, or identical strategy signatures for A and B.

### Generation records

A GenerationRequest is immutable and includes theorem_id, condition, proof_id or null, proof-text hash, prompt name/version/hash, rendered-prompt hash, model adapter, provider, exact model revision, sampling parameters, sample index, requested seed, capability flags, and deterministic request_id.

Derive request_id from a canonical serialization of all factors that could change the response:

    sha256(schema_version | theorem_id | statement_hash | import_hash |
           condition | proof_hash | prompt_hash | chat_template_hash |
           model_revision | sampling_json | sample_index)

A GenerationResponse stores request_id, timestamps, provider request ID when available, raw response path and checksum, mechanical extraction result and checksum, token counts, monetary cost, latency, transport attempt history, finish reason, and terminal status. Never place full raw responses inside the run manifest.

### Validation and evaluation records

LeanCheckResult stores statement-hash match, extraction status, parser status, elaboration status, exit code, wall time, peak memory when measurable, stdout/stderr artifact paths, declaration name, axiom list, prohibited-token findings, and a normalized failure category.

StrategyJudgment stores independent outputs from the signature extractor, auxiliary LLM judge, human annotators, and adjudication. It supports multiple strategy labels and the states match_A, match_B, mixed_or_alternative, and unresolved. Keep original labels after adjudication.

StepAlignment supports one-to-one, one-to-many, many-to-one, and implicit alignments. Each informal step may align to zero or more formal evidence spans or proof-term nodes with a confidence and explanation. CounterfactualEvaluation stores compilation, strategy match, step coverage, utilization state, ambiguity bounds, and derived theorem-level metrics without overwriting source judgments.

### Artifact layout and immutability

Every run has a content-addressed directory:

    outputs/runs/<run_id>/
      manifest.json
      environment.json
      requests.jsonl
      responses/<request_id>/raw.*
      responses/<request_id>/extracted.lean
      lean/<request_id>/candidate.lean
      lean/<request_id>/result.json
      evaluations/automatic.jsonl
      evaluations/llm_judge.jsonl
      evaluations/human.jsonl
      evaluations/adjudicated.jsonl
      derived/sample_metrics.parquet
      derived/theorem_metrics.parquet
      reports/

Write artifacts atomically through a temporary file followed by a same-filesystem rename. Verify the checksum before treating a request as complete. On resume, skip only verified terminal artifacts. Refuse to mutate a frozen run; create a child run with parent_run_id and a recorded reason.


## Interfaces and Implementation Boundaries

Expose a typed ModelAdapter protocol:

    class ModelAdapter(Protocol):
        @property
        def capabilities(self) -> ModelCapabilities: ...
        def generate(self, request: GenerationRequest) -> GenerationResponse: ...

ModelCapabilities declares support for proof conditioning, deterministic seeds, local inference, structured output, compiler-feedback repair, and token/cost reporting. Implement adapters for an OpenAI-compatible API, local Hugging Face or vLLM inference, ProofBridge, and ProofFlow when their public interfaces can be reproduced on the server. A provider adapter translates transport only; it must not change benchmark semantics.

Expose a LeanChecker:

    class LeanChecker:
        def check(self, candidate: LeanCandidate, limits: ResourceLimits) -> LeanCheckResult: ...

Expose evaluation boundaries:

    extract_strategy_signatures(candidate, theorem_spec) -> AutomaticStrategyEvidence
    align_steps(proof_variant, candidate, dependency_evidence) -> StepAlignmentSet
    classify_strategy(evidence, rubric) -> StrategyJudgment
    compute_sample_metrics(record, judgment) -> SampleMetrics
    aggregate_theorems(samples, analysis_spec) -> TheoremMetrics
    estimate_effects(theorems, analysis_spec) -> StatisticalReport

Keep prompt rendering, provider calls, Lean checking, annotation import, metric computation, and reporting as separate stages. Reporting must read frozen derived artifacts and never trigger model calls.


## Lean Validation and Dependency Inspection

Pin the exact Lean version in lean-toolchain and the exact Mathlib revision in lake-manifest.json. Lean 4.15 is provisional because both ProofBridge and ProofFlow document that version. Resolve the exact Mathlib tag and commit by compiling all pilot references and the selected specialized systems; record both, not only a floating release name.

For each candidate, construct a fresh Lean source file from a canonical header and the exact benchmark theorem declaration. The model supplies only the proof body. If a model emits the full declaration, the extractor may accept it only when the normalized declaration header and theorem type exactly match the canonical hash. The extractor may remove Markdown fences and select one unambiguous proof block. It may not add imports, repair syntax, rewrite tactics, choose the best of several proof bodies, or change the theorem.

Run each candidate in a fresh process with no network, a 120-second wall-clock timeout, a provisional 4 GB memory limit, fixed imports, and captured stdout, stderr, exit status, time, and memory. Keep Lean heartbeat limits finite and declared; never use unlimited heartbeats merely to turn timeouts into slow successes.

Before and after elaboration, reject sorry, admit, sorryAx, custom axiom declarations, unsafe trust bypasses, or native-decision shortcuts that introduce unreviewed trust. Run #print axioms or Lean.collectAxioms on the generated theorem. Permit and disclose only the standard Mathlib foundations expected for the item, commonly propext, Classical.choice, and Quot.sound. Fail closed on unknown axioms.

Build ProofFaithfulness/Dependency.lean as a small Lean metaprogram. For an elaborated theorem constant, obtain its value expression and use Lean utilities such as Expr.getUsedConstants or ConstantInfo.getUsedConstantsAsSet to list referenced declarations. Traverse expression binders and let expressions to determine whether explicitly introduced local facts occur in the final term. Supplement proof-term inspection with syntax-level tactic evidence for preregistered signatures.

The dependency prototype has at least five controlled fixtures:

1. an induction proof whose induction structure is used;
2. a ring or algebra proof with a recognizable normalization signature;
3. an explicit local lemma used downstream;
4. a decorative local lemma that compiles but is never used; and
5. a proof whose final automation bypasses the supplied intermediate steps.

Validate the extractor against controlled deletion: remove an alleged used local fact and confirm failure when the rest of the script is held fixed; remove an alleged unused fact and confirm the theorem still compiles. This is evidence for local utilization, not a universal logical-necessity oracle.

If normalized proof-term graph extraction cannot be made reliable during the pilot, freeze explicit local-step utilization as the workshop metric and record full graph recovery as a post-workshop extension. Do not delay the primary counterfactual result for an unreliable visualization.


## Prompt and Model Protocol

The theorem-only prompt asks for a Lean proof body for an exact supplied declaration and imports. The validity-only proof-conditioned prompt provides the informal proof as potentially helpful context but asks only for a valid proof. The preservation prompt explicitly asks the model to preserve the mathematical strategy and essential intermediate claims of the supplied proof while producing a valid Lean proof. Prompts state the prohibited placeholders and single-proof output format.

Paraphrases are drafted with model assistance only if desired, then edited by a human. They must preserve the same mathematical claims, dependency graph, and strategy signatures while changing surface wording. A second annotator validates the paraphrase without seeing which text is original.

Freeze prompt text and hashes before core inference. Model-specific chat templates are part of the adapter configuration and are also hashed. Store the exact API model ID or local weight revision, library versions, quantization, tensor parallelism, GPU type, context length, decoding parameters, date, region when relevant, and provider limits.

The model slate must represent:

1. at least one frontier general model available through an approved API;
2. at least one fully reproducible open-weight general or code model;
3. at least one specialized Lean theorem prover, such as a verified Kimina, DeepSeek-Prover-V2, or Goedel-Prover-V2 revision; and
4. ProofBridge and/or ProofFlow as proof-conditioned pipeline baselines if their released code can run in the pinned environment.

Do not hard-code this provisional list. Server GPU memory, licenses, API access, current model IDs, and smoke-test compatibility determine the exact frozen slate. Systems unable to consume a natural-language proof remain theorem-only baselines. Record failed integrations rather than silently omitting them.

Credentials enter only through environment variables or the server secret manager. Commit an .env.example containing names but no values. A preflight command reports missing variables by name and never prints secret contents. No secrets, prompts containing secrets, signed URLs, or provider headers may enter logs.


## Strategy, Step, and Utilization Evaluation

Strategy labels are hierarchical. A high-level label describes the mathematical family, such as induction, contradiction, extremal argument, algebraic normalization, combinatorial counting, or divisibility decomposition. A realization label captures the theorem-specific route. A generated proof matches a target when it exhibits an allowed high-level and realization path, satisfies the target's required signatures, avoids incompatible signatures, and falls within preregistered acceptable formal refinements.

Automatic evidence can include tactic and declaration use, theorem names, induction recursors, case structure, intermediate lemma statements, algebraic normalizers, rewriting direction, and proof-term constants. It supplies evidence, not final labels.

The auxiliary LLM judge receives the fixed theorem, one supplied informal proof, one generated Lean proof, the frozen rubric, and signature evidence. It is blinded to model, prompt style, sample number, other conditions, and expected A/B outcome. Its output is structured and versioned, but it never adjudicates its own disagreements.

Human evaluators receive the same relevant materials and are blinded to model, prompt, sample, and paired outputs. They judge individual outputs before seeing within-theorem pairs. Humans review every automatic-versus-LLM disagreement, every uncertain case, and a random 25 percent of the remaining outputs, with a minimum of 10 outputs when the pool is small.

Before production labels, both annotators independently label a five-theorem calibration set. They discuss disagreements, revise the written guidelines, then freeze the rubric. Calibration items are excluded from final inter-annotator agreement unless relabeled independently after the freeze.

For strategy and step labels, preserve both original annotations. Discussion produces consensus; if consensus fails, mark unresolved. Invite a third qualified expert only when the unresolved case materially affects the primary conclusion.

An informal step may map to multiple formal spans, several informal steps may collapse into one formal fact, and a step may be implicit. Do not require generated scripts to use have statements. Utilization states are used, unused, implicit, and unresolved. Step coverage is computed over strategy-essential steps; report logically necessary and explanatory steps separately.


## Metrics and Analysis

Let V_i(c, s) indicate that sample s for theorem i and condition c passes all Lean validity checks. Let M_i(c, s, A) and M_i(c, s, B) indicate adjudicated match to strategies A and B. Mixed or unresolved labels are handled through the frozen ambiguity policy, not dropped.

Report at least these sample- and theorem-level quantities:

1. Validity: the proportion passing exact-statement Lean validation.
2. Conditional target match: target-strategy match among valid outputs, clearly labeled as descriptive because conditioning on validity can select a different subset by condition.
3. Strict end-to-end pair responsiveness: for paired A/B samples, both compile and each matches its own target.
4. Directional discrimination:

       D_i = 0.5 * [(M_i(A, A) - M_i(B, A))
                  + (M_i(B, B) - M_i(A, B))]

   Here M_i(A, A) means match to A when conditioned on A, while M_i(B, A) means match to A when conditioned on B. Define the sample-pairing convention in the frozen analysis specification.
5. Proof-reliance lift over theorem-only:

       L_i = 0.5 * [(M_i(A, A) - M_i(0, A))
                  + (M_i(B, B) - M_i(0, B))]

6. Paraphrase invariance: the paired difference between original and paraphrased proof conditions.
7. Preservation-prompt effect: the paired difference between preservation and validity-only prompts.
8. Strategy-essential step coverage, explicit utilization, used-essential recall, and bypass rate.
9. Separate first-attempt and repair validity and responsiveness.

Do not collapse these into a single composite score. A model can be valid but unresponsive, responsive only when valid, or faithful to explicit steps while using a formally different realization; the report should show those distinctions.

The exact primary contrast and ambiguity coding remain an open research decision. The provisional primary is strict end-to-end A/B responsiveness, with proof-reliance lift over theorem-only as a supporting contrast and conditional responsiveness as descriptive. A statistician or methods reviewer must approve the final estimand before core results are inspected.

For confidence intervals, resample whole theorems with replacement so that all conditions, prompts, paraphrases, and samples for a theorem travel together. Use a fixed analysis seed and 10,000 bootstrap replicates unless simulation shows this is inadequate. Report theorem-level point estimates and 95 percent intervals.

Use a mixed-effects logistic model only as a secondary analysis, with theorem random intercepts and fixed effects for proof conditioning, prompt style, paraphrase, model, and prespecified interactions. At 30 theorem clusters, check convergence, singular fits, separation, and sensitivity; do not treat a fragile asymptotic p-value as primary evidence.

For unresolved judgments, the primary analysis conservatively codes the target claim as failure. Also report lower and upper bounds by assigning unresolved cases against and in favor of the target. Do not remove unresolved outputs.

Agreement statistics remain subject to methods review. The provisional report includes raw agreement and Gwet's AC1 for binary target-match labels; Jaccard similarity and label-wise precision/recall/F1 for multi-label strategy sets; edge F1 for proof-step dependency graphs; and nominal Krippendorff alpha for four-state utilization. Cohen's kappa is a sensitivity statistic, not the sole reliability claim.


## Milestones

### Milestone 0: Venue, server, and unresolved-decision discovery

The agent begins by running read-only environment discovery and writing outputs/environment/server.json. Capture operating system, CPU, RAM, GPU model/count/memory, storage quota and free space, scheduler and partition names, container support, outbound network rules, available Python/uv/Lean/Lake/CUDA versions, and secret-variable names. Do not print secret values.

In parallel, the human owner verifies a specific NeurIPS 2026 workshop and resolves the open estimand and agreement decisions. Coding may proceed on venue-independent infrastructure, but core results cannot be labeled primary before the analysis decisions are frozen.

Observable outcome: environment doctor emits valid JSON; the Human Plan names a venue or explicitly records the risk; the implementation records every unresolved decision as a gate rather than silently choosing it.

### Milestone 1: Reproducible scaffold

Create the Python package, Lean project, pinned lockfiles, CLI, configuration loader, logging, schemas, test layout, and continuous-check command. Make paths relative to a configured repository and artifact root. Add .env.example and a README quick start.

Observable outcome: from a clean environment, uv sync --frozen, lake build, formatting, lint, type checking, and unit tests pass. A deliberate missing secret produces a safe named error. Two identical canonical configurations produce the same run ID.

### Milestone 2: Trusted Lean checker

Implement canonical candidate assembly, the mechanical extractor, exact-statement hash comparison, isolated subprocess execution, limits, diagnostic normalization, prohibited-token scan, and axiom audit.

Test valid, syntax-invalid, type-invalid, timeout, out-of-memory where safely simulatable, statement-changing, sorry-containing, custom-axiom, multiple-block, and allowed-classical cases.

Observable outcome: valid fixtures pass; every prohibited or altered theorem fails with the intended category; candidate artifacts and diagnostics are retained; repeating a check is deterministic.

### Milestone 3: Pilot benchmark and references

Implement schema validation and curate five pilot pairs. Drafting may be agent-assisted, but humans must approve mathematical correctness, strategy separation, step roles, dependency edges, paraphrases, signatures, and reference proofs. Compile references in the pinned environment and audit axioms.

Use proof-strategy-pair-JOINT-CURATION-PLAN.md for the upstream discovery, source verification, extraction, proposition-only Lean checking, and human handoff. That plan does not require Lean proofs to approve the 30-pair curation set. The project lead must resolve its explicitly recorded policy difference with this milestone's later reference-proof gate before labeling a core benchmark frozen.

Observable outcome: data validate and lean check-references pass for all five items; a blinded second annotator can distinguish A and B by strategy; no pair is marked frozen without both approvals.

### Milestone 4: Dependency and utilization prototype

Build the Lean dependency utility and Python parser around the five controlled fixtures. Compare direct constant dependencies, binder use, syntax signatures, and deletion tests. Document failure modes caused by tactic elaboration and normalization.

Observable outcome: the prototype distinguishes an explicit used lemma from an unused decorative lemma and identifies the intended induction/algebra fixtures. The human gate selects either explicit utilization or a fuller dependency graph for the workshop analysis.

### Milestone 5: Generation harness and adapters

Implement canonical requests, prompt rendering, adapter capabilities, local/OpenAI-compatible transport, content-addressed responses, cost limits, retries, resume, and repair branching. Integrate the frozen model slate after server smoke tests.

Observable outcome: a dry run enumerates exactly the expected request cells with no duplicates; interrupted toy inference resumes without reissuing verified requests; invalid outputs remain retained and are not resampled; a provisional 500 USD aggregate API ceiling stops new paid requests at an approval gate.

For the frozen nine-cell matrix, a fully proof-conditioned model produces 27 first-attempt requests per theorem and therefore 135 requests for the five-theorem pilot or 810 for the 30-theorem core. A theorem-only model produces three requests per theorem: 15 for the pilot or 90 for the core. The plan-check command prints these counts per model, then lists every capability-based omission. Repair rounds and the optional robustness extension are separate counts.

The 500 USD figure is a planning ceiling, not permission to spend. The user or designated owner must explicitly approve each paid run batch.

### Milestone 6: Evaluation and annotation workflow

Implement deterministic signature extraction, blinded annotation export/import, structured auxiliary-judge output, disagreement queues, calibration support, adjudication, and agreement computation. Preserve original labels.

Observable outcome: fixtures cover match A, match B, mixed, unresolved, one-to-many step alignment, implicit step, used local fact, and unused local fact. Blinding checks confirm that bundles contain no model, prompt, condition, or sample identity leakage.

### Milestone 7: Five-pair pilot gate

Run the complete pilot with at least one reproducible open model and the selected proof-conditioned system, plus any approved API models. Produce validity, strict responsiveness, conditional responsiveness, signature evidence, utilization, ambiguity bounds, timing, and cost.

The pilot passes only when all references compile; the workflow runs end to end; at least one known faithful and one known unfaithful fixture are classified correctly; used and unused local facts are distinguished; annotators find the rubric manageable; and projected core runtime, cost, and human workload fit the deadline.

If the gate fails, diagnose the specific component and revise infrastructure or rubric. Do not change benchmark definitions after looking at model-favorable results without versioning the pilot as exploratory.

### Milestone 8: Freeze and core execution

Freeze schemas, prompts, benchmark records, model revisions, seeds, estimands, ambiguity rules, inclusion/exclusion rules, and analysis code hashes in a preregistration-style manifest. Then run the 30-pair core. Apply the precision expansion rule without conditioning on whether the observed result is favorable.

Observable outcome: the frozen manifest recreates the exact request list; all missing cells are accounted for; core reports are built without editing raw data; deviations are machine-readable and described in the paper.

### Milestone 9: Report and release

Generate model-by-condition validity, responsiveness, prompt-effect, paraphrase, coverage, utilization, robustness, cost, and failure-mode tables. Include theorem-level uncertainty, not sample-level pseudo-replication. Build plots with accessible labels and export source data.

Release code, schemas, permitted benchmark text, reference proofs, prompts, annotation guidelines, manifests, aggregate results, and permitted raw outputs regardless of whether the hypothesis is supported. Respect model-provider and source-dataset licenses.

Observable outcome: a fresh clone or clean allocation regenerates all public aggregate tables from released artifacts, and a reviewer can trace any reported cell back to theorem IDs and immutable request records.


## Concrete Commands

The exact server project path is intentionally open. After cloning or creating the repository, run from its root. The CLI executable is proof-faithfulness.

Initial environment and dependency setup:

    uname -a
    df -h .
    python3 --version
    uv --version
    lake --version
    nvidia-smi
    sinfo
    git status --short
    uv sync --frozen
    lake build
    uv run proof-faithfulness env doctor --output outputs/environment/server.json

Only the maintainer who creates or intentionally upgrades the Lean lockfile runs lake update, reviews the resulting lake-manifest.json diff, records the resolved Mathlib commit, and then commits it. Reproductions and reported runs use the committed manifest and do not run lake update. If a compatible Mathlib cache is available, use the cache-fetch command documented for the pinned release before lake build and record the exact command.

The discovery commands are read-only. nvidia-smi and sinfo are optional probes: record “not installed” when the target server has no NVIDIA driver or Slurm scheduler instead of treating that absence as an experiment failure. git status must succeed in the chosen project root; if no repository exists, stop and create or clone a correctly scoped project repository before generating research artifacts. The environment doctor succeeds with exit status zero and writes a JSON object containing status, operating_system, cpu, memory, gpu, storage, scheduler, toolchains, network_policy, and missing_secret_names. It must never contain secret values.

Validate pilot data and references:

    uv run proof-faithfulness data validate \
      --input data/benchmark/pilot.jsonl \
      --schema schemas/benchmark.schema.json
    uv run proof-faithfulness lean check-references \
      --benchmark data/benchmark/pilot.jsonl \
      --output outputs/reference_checks/pilot

Enumerate and inspect a pilot run before spending money:

    uv run proof-faithfulness generate plan \
      --config configs/experiment/pilot.yaml \
      --output outputs/plans/pilot.json
    uv run proof-faithfulness generate plan-check \
      --manifest outputs/plans/pilot.json

Run generation, Lean validation, and automatic evidence:

    uv run proof-faithfulness generate run \
      --manifest outputs/plans/pilot.json
    uv run proof-faithfulness lean check-run \
      --run-dir outputs/runs/<pilot_run_id>
    uv run proof-faithfulness proof inspect \
      --run-dir outputs/runs/<pilot_run_id>

Export blinded annotation bundles, import independent labels, and adjudicate:

    uv run proof-faithfulness annotate export \
      --run-dir outputs/runs/<pilot_run_id> \
      --output outputs/annotation_packets/pilot
    uv run proof-faithfulness annotate import \
      --run-dir outputs/runs/<pilot_run_id> \
      --input data/annotations/round1.jsonl
    uv run proof-faithfulness annotate agreement \
      --run-dir outputs/runs/<pilot_run_id>
    uv run proof-faithfulness annotate adjudicate \
      --run-dir outputs/runs/<pilot_run_id> \
      --input data/annotations/adjudicated.jsonl

Build analysis and report:

    uv run proof-faithfulness evaluate build \
      --run-dir outputs/runs/<pilot_run_id> \
      --analysis configs/analysis/frozen.yaml
    uv run proof-faithfulness report build \
      --run-dir outputs/runs/<pilot_run_id> \
      --output outputs/reports/pilot

Run repository checks before every reported run and release:

    uv run ruff format --check .
    uv run ruff check .
    uv run pyright
    uv run pytest -q
    lake build

Record real command output, exit status, wall-clock duration, and the run ID in this plan's Progress and Surprises sections. Replace placeholders only with actual IDs; do not commit fabricated transcripts.


## Testing and Acceptance Criteria

Unit tests cover canonical hashing, schema constraints, deterministic IDs, prompt hashes, extraction, status transitions, atomic writes, resume logic, budget gates, metric formulas, ambiguity bounds, bootstrap cluster resampling, and agreement measures.

Property tests or exhaustive fixtures verify that request enumeration contains each expected factor combination exactly once, reordering configuration keys does not change hashes, and changing any causal factor does change the request ID.

Lean integration tests cover successful compilation and every trust or resource failure category. At least one test confirms #print axioms output is parsed correctly. At least one test proves that a model cannot receive credit after changing the theorem.

Adapter contract tests use recorded or fake transports and never consume paid APIs. A separate opt-in smoke marker tests live providers. CI must exclude live and GPU tests by default and explain how to run them on the server.

Evaluation fixtures have expert-authored gold evidence for A, B, mixed, unresolved, used, unused, implicit, and bypass cases. Statistics tests compare small deterministic examples to hand-calculated values and confirm bootstrap resampling occurs by theorem rather than output.

The project is implementation-complete when:

1. all commands in the previous section succeed on the target server;
2. the five-pair pilot passes its scientific gate;
3. a frozen run manifest accounts for every requested and missing result;
4. no raw data or completed response is overwritten during resume;
5. all accepted Lean outputs prove the exact statement under the allowed axiom policy;
6. independent annotations, disagreements, and adjudications remain auditable;
7. the report reconstructs every number from versioned data and code;
8. all tests, formatting, linting, types, and Lean builds pass; and
9. a clean reproduction rebuilds the reported artifacts without hidden manual edits.


## Idempotence, Recovery, and Change Control

All planning, validation, evaluation, and reporting commands are safe to rerun. Generation is idempotent by deterministic request ID and verified checksum. A partially written artifact never counts as complete. A transport retry appends attempt metadata; it does not create a new scientific sample.

If a provider returns a different response for a repeated supposedly deterministic request, retain both transport artifacts, mark the request inconsistent, and exclude or bound it according to a frozen rule. Never overwrite the first response.

If a benchmark or prompt changes, increment its version and create a new run. If a reference theorem statement changes, all dependent requests and evaluations are invalidated by the statement hash. If an annotator rubric changes after calibration, version it and relabel affected items or mark analyses non-comparable.

Back up human-authored benchmark and annotation files through normal version control and server snapshots. Raw API artifacts may require encrypted research storage; record the storage policy and checksums in the manifest. Recovery procedures must not depend on provider logs remaining available.


## Risks and Scope Controls

The largest scientific risk is confusing mathematical strategy with superficial Lean syntax. Mitigate this through paired complete proofs, preregistered signatures, acceptable refinements, blinded experts, and multiple evidence sources.

The largest schedule risk is the unverified workshop-specific deadline. The Human Plan must resolve it immediately. If the deadline is too early, submit a rigorous five-pair pilot or target the next suitable venue; do not label automatically generated unreviewed pairs as trusted.

The largest engineering risk is integrating systems with different Lean versions and orchestration assumptions. Keep every adapter capability-explicit and record unsupported conditions. Prefer the common Lean 4.15 environment when possible, but isolate an external system if changing it would invalidate its published setup.

The largest statistical risk is few theorem clusters with many repeated outputs. Make the theorem the resampling unit, report uncertainty, and treat mixed models as secondary.

The largest measurement risk is overclaiming proof-term dependency analysis. Require controlled fixtures and deletion checks, publish limitations, and fall back to explicit utilization when necessary.

The largest resource risk is inference cost and server availability. Dry-run the full request count, estimate GPU-hours and API cost from the pilot, enforce approval gates, and allow the frozen model slate or benchmark size to shrink transparently before core execution.


## Related Work and Positioning

ProofBridge, by Prithwish Jana and colleagues, is an ICLR 2026 system for theorem-and-proof autoformalization using joint embeddings, retrieval, and iterative repair. It evaluates end-to-end success on a 244-item proof-augmented miniF2F test set under Lean 4.15. This project asks a different question: whether the output changes with one of two supplied correct strategies when the theorem is fixed. Source: https://arxiv.org/abs/2510.15681 and https://github.com/PrithwishJana/ProofBridge.

ProofFlow represents an informal proof as a dependency graph and formalizes its nodes with a graph builder, lemma formalizer, and tactic completer. Its released benchmark contains 184 undergraduate problems and it evaluates Lean validity and proof-graph coverage. This project adds the A/B counterfactual intervention and explicit comparison against theorem-only behavior. Source: https://arxiv.org/abs/2510.15981 and https://github.com/Huawei-AI4Math/ProofFlow.

StepProof checks natural-language proofs step by step in Isabelle using earlier sentences as context. It motivates local verification but does not test two complete strategies for the same fixed theorem. Source: https://arxiv.org/abs/2506.10558.

RobustPABench studies Lean 4 autoformalization under global paraphrases and local edits of numbers, symbols, and proof steps. The proposed experiment complements it by using two fully correct proofs that deliberately differ in strategy, plus a smaller invalid/mismatched extension. Source: https://arxiv.org/abs/2606.14867 and https://github.com/ucr-rai/robust-proof-autoformalization.

ProofNet, NaturalProofs, and LeanDojo provide useful source material or contamination baselines, but the verified public descriptions do not provide the required curated A/B proof pairs as a ready-made benchmark. Sources: https://openreview.net/forum?id=Zix86UbMGh, https://zenodo.org/records/4632539, and https://arxiv.org/abs/2306.15626.

Lean's proof-validation and API documentation support axiom auditing and used-constant inspection. Sources: https://lean-lang.org/doc/reference/latest/ValidatingProofs/ and https://lean-lang.org/doc/api/Lean/Util/FoldConsts.html.

The official NeurIPS 2026 workshop call gives organizer-level timing but delegates contributed-paper rules to individual workshops. Source: https://neurips.cc/Conferences/2026/CallForWorkshops.


## Open Decisions That Must Remain Visible

The following are not permission for the implementation agent to invent a paper claim. The Human Plan assigns owners and deadlines:

1. the exact NeurIPS 2026 workshop, contributed-paper deadline, scope, page limit, and archival policy;
2. the exact primary statistical contrast, pairing convention across three samples, and ambiguity coding;
3. the final agreement-statistic set and acceptable reliability threshold;
4. the exact server path, scheduler, storage, GPUs, network policy, and secret mechanism;
5. the final Lean 4.15-compatible Mathlib tag and commit;
6. the final model IDs, revisions, licenses, quantization, and decoding settings;
7. whether full dependency graphs pass the pilot or explicit-step utilization becomes the workshop metric;
8. which source theorems are sufficiently unfamiliar or newly adapted to limit contamination;
9. whether the 10-item corrupted/mismatched extension fits the submission schedule; and
10. whether the secondary theorem-plus-proof autoformalization track fits after the primary fixed-theorem track is secure.


## Revision Note

2026-07-22: Initial ExecPlan written after the full design interview and source verification. It incorporates the accepted fixed-theorem A/B intervention, symmetric conditions, pilot/core scope, server-first setup, human gates, open statistical and agreement decisions, and NeurIPS 2026 workshop target.
