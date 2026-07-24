# Notes: Proof-Conditioned Faithfulness Planning

## Repository Facts

- The workspace currently contains shared planning and research-code standards, not a Lean project or evaluation implementation.
- `.agent/PLAN.md` requires a self-contained living ExecPlan with `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` sections.
- `RESEARCH_CODE_STANDARD.md` treats code that produces paper-reported numbers as library-tier code requiring tests, typed public interfaces, linting, boundary assertions, reproducibility metadata, and review.
- The implementation will ultimately run on a server whose environment and repository path have not yet been specified.

## Accepted Experimental Decisions

- Primary contribution: evaluation benchmark, not a new trained model.
- Primary claim: changing the supplied proof strategy should cause the corresponding change in the generated Lean proof.
- Primary track: fixed trusted Lean theorem; model generates only the proof.
- Secondary track: full theorem-plus-proof autoformalization.
- Benchmark: five-pair pilot; 30-theorem core; possible expansion toward 50 based on interval precision.
- Two proof variants per theorem by default; a third only where it adds a genuinely distinct strategy.
- Core domains: elementary number/integer reasoning, finite sums/sets, elementary algebra/divisibility/inequalities.
- Core conditions: theorem-only, proof A, proof B, paraphrase A, paraphrase B.
- Prompt styles: preservation and validity-only for proof-conditioned cases.
- Sampling: three generations per condition and prompt, paired seeds where available.
- Primary track is first-attempt; two compiler-feedback repair rounds are a secondary track.
- Corrupted and mismatched proofs are a preregistered ten-theorem extension that cannot delay the core paper.
- Evaluation reports validity, conditional paired responsiveness, and end-to-end responsiveness separately.
- Strategy matching uses predeclared labels plus required, incompatible, and acceptable structural signatures.
- Step alignment is semantic and may be one-to-many or many-to-one.
- Step utilization uses proof dependencies and safe deletion tests, with used/unused/implicit/unresolved outcomes.
- Human annotation uses two qualified annotators on at least 25% or ten theorem pairs, after a five-theorem calibration set.
- API-cost planning ceiling is $500, with an explicit approval gate; this is not spending authorization.
- Target system categories: frontier general model, open-weight model, specialized Lean prover, and proof-conditioned pipeline.
- Raw outputs are immutable; derived tables are reproducible; run manifests record dataset, code, prompt, model, and sampling versions.
- Final deliverables: one coding-agent ExecPlan and one human plan.

## Intentionally Open Questions

- Q38: exact preregistered primary statistical contrasts, pending methodology and pilot review.
- Q44: exact inter-annotator agreement statistics for hierarchical, multi-label strategy and graph annotations.
- Current model list and compatibility.
- Exact Lean/Mathlib pin, to be chosen after model compatibility testing.
- Server environment, scheduler, storage, secret management, and final project path.
- Exact NeurIPS 2026 workshop and verified submission deadline.

## Sources

### ProofBridge

- Canonical metadata: [arXiv:2510.15681](https://arxiv.org/abs/2510.15681), v3 dated 2026-03-29. Title: *ProofBridge: Auto-Formalization of Natural Language Proofs in Lean via Joint Embeddings*. Authors: Prithwish Jana, Kaan Kale, Ahmet Ege Tanriverdi, Cruise Song, Sriram Vishwanath, and Vijay Ganesh. Published at ICLR 2026.
- Scope: end-to-end natural-language theorem-and-proof translation to Lean 4, using joint theorem+proof embeddings, retrieval-augmented fine-tuning, and iterative repair.
- Evaluation: `MINIF2F-TEST-PF` has 244 instances on Lean 4.15.0. Type correctness checks the generated theorem and proof; semantic correctness is a Lean-checked LLM-generated bidirectional-equivalence certificate for theorem statements. Results use pass@k through 32.
- Boundary for this project: theorem equivalence and successful proof checking do not establish that the generated formal proof used the supplied informal strategy.
- Code: [ProofBridge repository](https://github.com/PrithwishJana/ProofBridge), MIT licensed, documents Lean 4.15.0 and Slurm/H100 usage but has no tagged release.

### ProofFlow

- Canonical metadata: [arXiv:2510.15981](https://arxiv.org/abs/2510.15981), v1 dated 2025-10-13. Correct title: *ProofFlow: A Dependency Graph Approach to Faithful Proof Autoformalization*. Authors: Rafael Cabral, Tuan Manh Do, Xuejun Yu, Wai Ming Tai, Zijin Feng, and Xin Shen.
- Scope: constructs a natural-language proof DAG, formalizes nodes as Lean lemmas, and completes each lemma with tactics. Structural fidelity is explicitly part of ProofScore.
- Benchmark: 184 undergraduate problems across six areas, averaging 8.4 graph nodes. The benchmark contains one supplied proof graph per problem, while allowing multiple valid graph granularities.
- Evaluation: Lean 4.15.0, pass@1/3/5 with compiler-feedback retries; the main reported pass@5 ProofScore is 0.545 and proof-level syntactic success 0.375 for the thinking DAG configuration.
- Boundary for this project: ProofFlow evaluates whether one output follows one supplied proof graph. It does not perform the same-theorem intervention between complete, correct, strategy-distinct proofs.
- Code: [ProofFlow repository](https://github.com/Huawei-AI4Math/ProofFlow), MIT licensed, Python package with local or remote Lean server support and adapters for API/vLLM models.

### StepProof

- Canonical metadata: [arXiv:2506.10558](https://arxiv.org/abs/2506.10558), v2 dated 2025-06-30. Title: *StepProof: Step-by-step verification of natural language mathematical proofs*. Authors: Xiaolin Hu, Qinghua Zhou, Bogdan Grechuk, and Ivan Y. Tyukin.
- Scope: sentence-level formalization and verification using Isabelle rather than Lean. Each step is verified as a subproof and, as described by ProofFlow, earlier steps are available to later steps without a hand-annotated dependency DAG.
- Boundary for this project: local step verification does not test whether a model distinguishes multiple valid complete strategies for one theorem.

### RobustPABench

- Canonical metadata: [arXiv:2606.14867](https://arxiv.org/abs/2606.14867), dated 2026-06-12. Title: *Evaluating the Robustness of Proof Autoformalization in Lean 4*. Authors: Zhengtao Gui, Sheng Yang, and Zhouxing Shi. ICML 2026 AI4Math workshop poster.
- Scope: global meaning-preserving proof rewrites and local number, symbol, or proof-step edits. It reports sensitivity to paraphrases and whether outputs reflect targeted local changes.
- Benchmark: miniF2F (244) plus MATH-500 (500); public dataset configurations include original, four global paraphrase/step-rewrite variants, and five local-edit variants.
- Boundary for this project: targeted local edits can change mathematical content or invalidate a proof. The proposed benchmark instead replaces an entire valid proof with a different valid mathematical strategy while holding the theorem fixed.
- Code/data: [repository](https://github.com/ucr-rai/robust-proof-autoformalization) and [RobustPABench](https://huggingface.co/datasets/ucr-rai/RobustPABench), both currently available.

### Existing Datasets

- ProofNet has 371 undergraduate examples, each with one Lean 3 statement, one natural-language statement, and one natural-language proof: [OpenReview metadata](https://openreview.net/forum?id=Zix86UbMGh).
- NaturalProofs has roughly 20,000 natural-language theorem/proof records sourced from ProofWiki: [Zenodo record](https://zenodo.org/records/4632539).
- LeanDojo has 98,734 Mathlib theorem/proof records and premise annotations, but no paired informal strategy variants: [arXiv:2306.15626](https://arxiv.org/abs/2306.15626).
- No verified adjacent benchmark found in this search intentionally supplies multiple complete, correct, strategy-distinct natural-language proofs for the same fixed Lean theorem. Existing resources may seed theorem selection, but the paired proofs and annotations must be newly curated.

### Current Model and Pipeline Candidates

- ProofBridge and ProofFlow are public proof-conditioned system candidates; both are most directly compatible with Lean 4.15.0.
- `AI-MO/Kimina-Prover-RL-1.7B` is a small reproducible specialized Lean prover, but its intended task is proving an already formalized theorem, so it should be a theorem-only control unless a proof-conditioned interface is validated. [Official AI-MO model collection](https://huggingface.co/collections/AI-MO/kimina-prover).
- DeepSeek-Prover-V2 publishes 7B and 671B Lean prover models; the 7B candidate is feasible on a modest GPU server and is theorem-proving rather than proof-autoformalization. [Official repository](https://github.com/deepseek-ai/DeepSeek-Prover-V2).
- Goedel-Prover-V2 publishes 8B and 32B Apache-2.0 models; the 32B weights are approximately 65.5 GB. [Official model card](https://huggingface.co/Goedel-LM/Goedel-Prover-V2-32B).
- Exact frontier and open-weight general-model identifiers must be selected after server/API discovery and frozen before the full run. The harness should support provider APIs and an OpenAI-compatible local vLLM endpoint without embedding model IDs in code.

### Lean Tooling

- Lean can audit transitive theorem axioms with `#print axioms`; only `propext`, `Classical.choice`, and `Quot.sound` are treated as standard benign axioms. `sorryAx`, compiler-trust/native-decision axioms, and custom axioms must be separately reported. [Lean proof-validation reference](https://lean-lang.org/doc/reference/latest/ValidatingProofs/).
- The current Lean API exposes `Lean.Expr.getUsedConstants`, `Lean.Expr.getUsedConstantsAsSet`, and `Lean.ConstantInfo.getUsedConstantsAsSet` through `Lean.Util.FoldConsts`, allowing direct-constant extraction from elaborated theorem values. [Lean API](https://lean-lang.org/doc/api/Lean/Util/FoldConsts.html).
- `Lean.collectAxioms` collects transitive axiom dependencies. It is useful for trust auditing, not as the full theorem-dependency graph.
- Tactic syntax alone cannot recover strategy reliably because elaboration lowers tactics into proof terms and automation may synthesize large terms. The five-proof prototype must compare syntax features, direct constants in elaborated values, and explicit-step ablation.
- Lean 4.15.0 is the provisional compatibility pin because both ProofBridge and ProofFlow evaluate there. The exact Mathlib commit remains a server smoke-test decision; upgrading to current Lean 4.30+ would make direct reproduction harder.

### Statistical Design Research

- Repeated samples and conditions from one theorem are dependent; theorem-level resampling is therefore the appropriate primary bootstrap unit. Mixed-effects logistic regression can model binary repeated observations with theorem random intercepts, but with 30 clusters it should remain secondary and receive convergence diagnostics.
- Provisional primary estimands are: end-to-end paired responsiveness; proof-conditioning lift relative to theorem-only outputs; and the preservation-prompt effect. Conditional responsiveness among only pairs that compile is descriptive because conditioning on post-generation validity can select a non-comparable subset.
- Report paired theorem-cluster bootstrap confidence intervals for marginal effect sizes. Use a generalized linear mixed model only for secondary model-by-condition interactions.
- Q38 remains a human/statistician approval gate because the exact strict-pair and directional counterfactual estimands must be frozen before the full run.

### Annotation Agreement Research

- [Artstein and Poesio (2008)](https://aclanthology.org/J08-4004/) survey kappa- and alpha-style agreement and caution that complex annotations need metrics matched to their structure.
- [Gwet (2008)](https://bpspsychub.onlinelibrary.wiley.com/doi/abs/10.1348/000711006X126600) introduces AC1 as a more stable nominal agreement coefficient when prevalence is extreme.
- [Passonneau (2006)](https://www.cs.columbia.edu/nlp/papers/2006/passonneau_06.pdf) introduces MASI distance for set-valued annotations.
- Provisional Q44 recommendation: raw agreement plus Gwet AC1 for binary strategy-match labels; instance Jaccard and label-wise F1 for multi-label strategies; edge F1 for graphs; nominal Krippendorff alpha for used/unused/implicit/unresolved utilization. Keep Cohen kappa as a familiar sensitivity analysis. Require statistician or methods-review confirmation before preregistration.

### NeurIPS 2026 Workshop Feasibility

- Official NeurIPS guidance gives a suggested workshop-contribution deadline of **2026-08-29 AoE** and a mandatory workshop decision deadline of 2026-09-29. Workshops occur 2026-12-11 through 2026-12-13 across Sydney, Paris, and Atlanta: [official call](https://neurips.cc/Conferences/2026/CallForWorkshops).
- The suggested deadline is not a universal paper deadline; each accepted workshop sets its own call, page limit, archival status, and date.
- As of 2026-07-22, a directly matching AI-for-mathematics/formal-reasoning NeurIPS 2026 workshop call was not yet verified in indexed official/OpenReview results. Venue selection remains an urgent human task.
- The NeurIPS target is schedule-risky: roughly five weeks remain until the suggested date. The plan must use a five-pair minimum submission path, require a venue decision within days, and must not fabricate a complete 30-theorem benchmark if quality gates cannot be met.

## Final Deliverables and Audit

- Created `proof-conditioned-faithfulness-EXECPLAN.md`, a self-contained living ExecPlan for the coding agent with dated progress checkboxes, scientific contract, target repository structure, typed data and adapter interfaces, Lean trust checks, model/prompt protocol, metrics, statistical analysis, nine implementation milestones, exact CLI commands, tests, acceptance criteria, recovery rules, risks, source positioning, and visible open decisions.
- Created `proof-conditioned-faithfulness-HUMAN_PLAN.md`, a checkbox-driven human plan with dated progress, a five-week workshop sprint, seven human approval gates, a plain-language annotator definition, annotation workflow, open-research tracking for Questions 38 and 44, venue/server/model/toolchain questions, accepted decisions, role assignments, and paper/release checks.
- Audited Markdown heading spacing, required ExecPlan section presence, local file references, trailing whitespace, and the rule that ExecPlan checkboxes appear only in `Progress`.
- Audited the implementation plan against `RESEARCH_CODE_STANDARD.md`: raw data is read-only, experiments record seeds/config/data versions, paper-bound code is promoted into `src/`, public interfaces are typed and documented, boundary invariants fail loudly, and Ruff/Pyright/pytest/Lean checks are required.
- Discovered that this planning workspace has no `.git` directory. The server implementation must begin in a correctly scoped new or cloned repository; the plan explicitly warns against initializing Git in an unrelated server directory.

## Joint Agent–Human Curation Plan

- Added `proof-strategy-pair-JOINT-CURATION-PLAN.md` on 2026-07-23 to connect automated source discovery and Lean-statement preparation with human mathematical and provenance review.
- The target is 30 approved A/B strategy pairs. The agent first discovers 45–60 candidates because some will fail source, equivalence, strategy-distinctness, copyright, duplication, or Lean-statement review.
- Each proof strategy must be supported by an inspected, traceable, human-authored mathematical source. Preferred sources are published textbooks, peer-reviewed expositions, named university notes, mathematical-society publications, and verifiable mathematician-authored sites.
- Search snippets, AI-generated sources, anonymous solution dumps, and model memory are not evidence.
- The public dataset stores structured source-faithful paraphrases by default, with citations, precise locators, license state, and checksums. Restricted full-text snapshots stay out of the public repository.
- The agent translates the shared theorem into a Lean proposition and records imports, toolchain, elaboration result, diagnostics, and hashes. No Lean proof is required during this 30-pair curation stage.
- Human reviewers approve source quality, mathematical correctness, same-theorem equivalence, strategy distinctness, and informal-to-Lean fidelity. Reviews bind to exact record hashes; edits require a new version and reapproval.
- The earlier plans require compiling reference Lean proofs at benchmark freeze. The new curation plan records this as a visible policy mismatch that the project lead must resolve before a core benchmark is called frozen.
