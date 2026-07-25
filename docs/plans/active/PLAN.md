# PLAN: Counterfactual Faithfulness in Proof-Conditioned Lean Autoformalization

This is the living implementation plan, maintained in accordance with
[docs/plans/PLANS.md](../PLANS.md) (the repo-owned ExecPlan standard — read it if this
is your first session). It supersedes `proof-conditioned-faithfulness-EXECPLAN.md`,
HUMAN_PLAN, JOINT-CURATION-PLAN, and task_plan (retired 2026-07-24 with SUPERSEDED
banners in ../completed/ — **this file alone controls implementation**). The agent
executing this plan must keep the Progress, Surprises & Discoveries, and Decision Log
sections current, with a date on every entry. The project
is complete only when the acceptance criteria pass — creating files without running the
checks is not completion.

Structure: **Part 1 PRE-SERVER** (laptop: curation and decisions only — this machine
cannot hold the Lean toolchain; no local code execution), **Part 2 SERVER** (all coding
and all runs), **Part 3 POST-SERVER** (annotation, analysis, release, after generation
runs complete). GitHub is the bridge: laptop pushes curation + plans; server clones and
executes.

Engineering standards are NOT restated here — every coding task on any part follows
[coding-standard/](../../../coding-standard/) (CODING.md when writing, CODE_REVIEW.md when
reviewing, style/research.md as the ML add-on review pass, README.md for tiers/stakes
gate/todo.md protocol). The agent entry map is [AGENTS.md](../../../AGENTS.md).

## Purpose and Research Outcome

Build and run a reproducible benchmark asking: when a model receives one of two
different, complete, correct informal proofs of the same fixed theorem, does its
generated Lean proof follow the supplied proof's mathematical strategy?

The primary experiment holds the trusted Lean theorem statement fixed. For each theorem,
humans approve two informal proofs, A and B, with genuinely different strategies. The
benchmark measures: (1) compilation validity; (2) strategy match to the conditioned
proof; (3) coverage of strategy-essential steps; (4) whether formalized steps are
actually used in the proof term; (5) whether switching A→B switches the generated
strategy correspondingly. The artifact is an evaluation framework and paired benchmark,
not a trained model.

**Venue (decided 2026-07-24): MATH-AI workshop @ NeurIPS 2026, Atlanta.** Contributed
papers due **September 25, 2026 AoE**; notification October 19; 4 pages + unlimited
references/appendix; non-archival; previously published work prohibited.
Source: https://mathai-2026.github.io/cfp. **Fallback: VERICODEGEN** (same conference;
deadline September 10; Lean/autoformalization explicitly in scope;
https://vericodegen.github.io/) — fallback go/no-go decision by ~September 5.

## Progress

- [x] 2026-07-22: Original design interview, related-work verification, first ExecPlan.
- [x] 2026-07-24: Project repo scaffolded (`proof-conditioned-faithfulness/`), agent-first
      layout, coding-standard kit, AGENTS.md map, git initialized.
- [x] 2026-07-24: Venue verified and decided — MATH-AI primary, VERICODEGEN fallback.
- [x] 2026-07-24: Condition matrix tiered (T1-T4); pilot scope = Tier 1+2 with human
      checkpoint between tiers; robustness extension postponed post-submission.
- [x] 2026-07-24: Analysis decisions deliberately deferred with hard freeze gate —
      see docs/design-docs/analysis-decisions-pending.md (todo T006).
- [x] 2026-07-24: Benchmark curation started — 15 candidate pairs drafted (batches 1-5)
      awaiting human review in data/benchmark/candidates/; reusable DISCOVERY-PROMPT.md
      created for external agents (Codex); exclusion list current through 015.
- [x] 2026-07-24: Codex external review of this plan incorporated (grill session):
      uv bootstrap done on laptop (pyproject.toml + uv.lock committed — server runs
      `uv sync --frozen` as written); control plane specified in
      docs/SERVER-HARNESS-RUNBOOK.md (SLURM confirmed as the scheduler); planning
      standard checked in at docs/plans/PLANS.md; ARCHITECTURE.md and gated
      EXPERIMENT-SPEC.md stub added; Tier 2 labeled exploratory; dispute rule added as
      analysis decision (g); S1-S5 given explicit run/expect exit criteria.
- [x] 2026-07-24: Codex-external discovery batch reviewed and filed — 4 keepers
      renumbered 016-019 (odd-divisors-iff-square, hockey-stick, Bernoulli,
      2-var Cauchy-Schwarz; all 8 sources verified by direct fetch, one dead
      secondary link flagged), 1 duplicate (gcd·lcm, filed as 020 with reject
      recommendation). Pool now 001-020. Ordered readiness gates P/S/C/A added to
      Part 2 (pilot-pair validation by every component, then API smoke, before any
      full run).
- [x] 2026-07-24: Opus discovery round 2 (3 agents: counting, parity/invariants,
      algebra) filed as 021-029. Claude-recommended keepers: 023 (3-set
      inclusion-exclusion), 024 (permutation product parity), 027 (Euler binary
      product); bench: 021, 022, 026, 029; reject-leaning: 025, 028 (verbatim
      Mathlib lemmas — retained as library-collapse fixtures for S5). Pool now
      001-029, all draft, awaiting human review. Discovery agents now report an
      Automation/library caveats field (three exact-Mathlib collapses caught at
      sourcing time this round).
- [x] 2026-07-24: Opus discovery round 3 (6 agents: modular, digits/sums,
      order/well-ordering, irrationality, discrete inequalities; 1 low-contamination
      agent lost to a session usage limit) filed as 030-044. Claude-recommended
      keepers: 031, 033, 036, 040, 041, 042; NOTES-library-collapse-catalog.md added
      (Loogle-verified list of theorems dead to exact Mathlib lemmas + the
      asymmetric-collapse and third-route-attractor taxonomies for the S5 rubric).
      Pool complete at 001-044 pending human review; discovery paused.
- [ ] YYYY-MM-DD: Human review of candidate pool; first 5 pilot pairs approved.
- [ ] YYYY-MM-DD: Full curation metadata (signatures, steps, paraphrases) for pilot 5.
- [x] 2026-07-24: GitHub remote created and pushed (T004); GitHub is now the source of
      truth for server checkouts.
- [x] 2026-07-24: Server access confirmed; environment discovery run. Compute-node
      outbound network works; project quota/purge policy and secret delivery remain T008.
- [x] 2026-07-24: Server scaffold built: frozen Python 3.12 uv environment, Lean 4.15.0,
      and Mathlib v4.15.0 at commit 9837ca9d65d9de6fad1ef4381750ca688774e608;
      Mathlib cache retrieval and `lake build` passed on the Klone dev/test host.
- [x] 2026-07-25: S1 complete. Data contracts and JSON Schemas, deterministic request
      IDs, the content-addressed artifact store, and CLI scaffolding passed unit tests,
      Ruff, Pyright, CLI help, and Lean build checks.
- [x] 2026-07-25: S4 adapter foundation complete: strict model configs, deterministic
      mock inference, OpenAI-compatible local-vLLM transport, and ProofBridge/ProofFlow
      JSON subprocess wrappers pass offline adversarial smoke tests. The package builds
      as wheel/sdist; the preflight suite passes 91 tests, Ruff, Pyright, and `lake build`.
      Independent review approved the adapter scope after identity, cardinality, size,
      secret, and process-lifecycle hardening.
- [ ] 2026-07-25: S4 remains in progress: generation orchestration, atomic budget
      permits, retry/resume integration, and complete mock run-directory tests remain.
      This does not pass S4, Gate C, or Gate A; real-model smoke checks have not run.
- [ ] YYYY-MM-DD: Gate S inputs ready: the five human-approved pilot statements and all
      ten reference proofs parse/elaborate, compile, pass the axiom audit, and receive
      human approval.
- [ ] YYYY-MM-DD: Implementation stages S1-S5 complete with tests (Part 2.3).
- [ ] YYYY-MM-DD: Model slate smoke-tested and frozen (needs API keys on server).
- [ ] YYYY-MM-DD: Pilot smoke slice (1-2 theorems) run and human-reviewed.
- [ ] YYYY-MM-DD: Full pilot (5 pairs, Tier 1) run; human checkpoint; Tier 2 run.
- [ ] YYYY-MM-DD: Pilot gate passed; analysis decisions frozen (T006 closes).
- [ ] YYYY-MM-DD: Preregistration-style freeze manifest; core smoke slice; core run
      (30 pairs, Tier 1) with per-batch spend approval.
- [ ] YYYY-MM-DD: Annotation complete (needs second annotator, T007); adjudication and
      agreement computed.
- [ ] YYYY-MM-DD: Analysis + report built from immutable artifacts; paper submitted to
      MATH-AI (Sept 25 AoE hard deadline).
- [ ] YYYY-MM-DD: Publish gate (style/research.md §5) passed; release; retrospective.

## Surprises & Discoveries

- 2026-07-24: NeurIPS 2026 has 66 accepted workshops; only two fit this project
  (MATH-AI, VERICODEGEN). MATH-AI's real deadline is Sept 25 — four weeks later than
  the Aug 29 assumption the old plan's schedule pressure was built on. The 30-pair core
  is therefore more feasible than previously believed.
  Evidence: OpenReview group listing NeurIPS.cc/2026/Workshop/*; mathai-2026.github.io/cfp.
- 2026-07-24: Two of six initial candidates (002 √2, 005 Σ C(n,k)) have exact or
  near-exact Mathlib lemmas — "close the goal with a library call" is a real third
  behavior beyond strategy-A/strategy-B, and the signature rubric must define how
  library-lookup outputs are coded (provisionally: mixed_or_alternative, never a match).
  Evidence: `irrational_sqrt_two`, `Nat.sum_range_choose` in Mathlib; see candidate
  Review notes.
- 2026-07-24: Automation tactics (`omega`, `decide`) can collapse either strategy into
  a one-liner on ℤ/mod candidates (001, 003) — signatures must key on discriminating
  lemmas, not tactic names alone.
  Evidence: candidate files 001/003 Review notes (discovery-agent caveats).
- 2026-07-24: This cluster's base image lacks `libatomic.so.1`, which Pyright's
  bootstrapped Node runtime requires; `module load gcc/12.3.0` supplies it. Mathlib's
  static curl also needs `SSL_CERT_FILE=/etc/pki/tls/certs/ca-bundle.crt` or every cache
  request fails with an OpenSSL "unregistered scheme" error. Both are recorded in the
  server runbook. Evidence: Pyright loader error; cache retry downloaded 5,826/5,826.
- (Carried from 2026-07-22:) closest verified systems — ProofBridge, ProofFlow,
  StepProof, RobustPABench — none compare two complete correct strategy-distinct proofs
  for the same fixed theorem; Lean 4.15 is the provisional interoperability version
  (both ProofBridge and ProofFlow use it).

## Decision Log

Decision owner is Tingxuan; recording author is the agent. Key standing decisions
(2026-07-22, carried): counterfactual responsiveness is the primary claim; validity /
conditional / strict metrics reported separately; 5-pair pilot, 30-pair core,
preregistered precision rule toward 50; first-attempt track primary with repair track
(≤2 rounds) separate; immutable raw outputs, transport retries only, never best-of;
sorry/admit/custom axioms rejected, standard Mathlib classical axioms disclosed;
Python 3.12 + uv + Pydantic + Typer + pytest + Ruff + Pyright + Lean 4 + Mathlib.

New decisions (2026-07-24, from the plan-restructuring walkthrough):

- Venue: MATH-AI primary / VERICODEGEN fallback (details in Purpose section).
- Laptop has no room for the Lean toolchain: ALL code development and execution moves
  to the server; pre-server work is curation, decisions, and repo publication only.
- Condition tiers: T1 = {theorem_only, proof_a, proof_b} preservation prompt;
  T2 = +{proof_a_validity, proof_b_validity}; T3 = +paraphrases (preservation);
  T4 = +paraphrase×validity. 3 samples per cell always. Runs are additive by
  deterministic request ID — later tiers never invalidate earlier artifacts.
- Pilot = Tier 1, human checkpoint reviewing outputs, then Tier 2. Core = Tier 1 first.
- Smoke-slice rule: every paid batch (pilot or core) starts with 1-2 theorems run
  end-to-end and human-reviewed before the full batch fires.
- Robustness extension (corrupted/mismatched proofs): postponed until after the MATH-AI
  submission.
- Reference Lean proofs: required for the 5 pilot pairs only (agent-drafted on server,
  human-approved); core pairs freeze on statement + signatures, with reference proofs
  added only where strategy expressibility is disputed. (Resolves the old
  curation-vs-Milestone-3 policy conflict.)
- Analysis decisions (primary estimand, sample pairing, ambiguity coding, uncertainty
  method, agreement threshold): deferred to post-pilot with provisional recommendations
  recorded in docs/design-docs/analysis-decisions-pending.md. HARD GATE: frozen before
  core results are inspected (T006).
- Curation format: Markdown-first (one file per pair, human-reviewable), best-effort
  JSONL alongside, schema validation server-side. Benchmark/annotation data are
  versioned; only data/raw/ is gitignored.
- Model slate: 4 required categories (frontier API; open-weight reproducible;
  specialized Lean prover; ProofBridge/ProofFlow pipeline). Exact IDs frozen at server
  smoke-test time. Specialized provers support temperature sampling; documented decoding
  recipes are respected and deviations recorded; identical samples at low temperature
  are retained as valid data (never resampled for diversity).
- Budget: $500 aggregate API planning ceiling; every paid batch needs explicit human
  approval; the ceiling is a stop-gate, not permission.
- Candidate review protocol: agents propose (Status: draft), human approves/rejects;
  every candidate file ends with a Review notes section (contamination reasoning,
  formalization caveats, approval-scrutiny pointers).

New decisions (2026-07-24, from the Codex-review grill session):

- Bootstrap vs. reproducible setup split: pyproject.toml + uv.lock are created and
  committed from the LAPTOP (done — `uv lock`, 37 packages, Python 3.12); the lockfile
  is laptop-owned. The server only ever runs `uv sync --frozen` and never `uv lock`.
- Server scheduler confirmed: SLURM. All operational procedure (job lifecycle,
  run-state machine, worker locks, rate limits, approval records, event logs,
  recovery) is normative in docs/SERVER-HARNESS-RUNBOOK.md, not restated here.
- **Tier 2 and above are exploratory/hypothesis-generating.** All confirmatory claims
  come from Tier 1. Rationale: the run-Tier-2 decision is made after inspecting Tier-1
  results, so Tier 2 cannot be confirmatory without a pre-frozen trigger rule we have
  no data to set. The human checkpoint stays a free judgment call.
- "Disputed core case" (the trigger for adding reference Lean proofs during core
  annotation) gets a mechanical definition, frozen at T006 as decision (g) in
  analysis-decisions-pending.md — never an informal judgment after seeing results.
- Old plans retire (move to completed/ with SUPERSEDED banners) + full git commit at
  T009, after the user signs off on this reworked plan.
- Budget reality (2026-07-24, supersedes the $500 planning ceiling): cluster =
  Tillicum (UW), $250 in compute credits (GPU jobs only — Lean checking is CPU;
  dev is mock-adapter/CPU only; prefer ≤32B open-weight models); frontier API =
  $20 credit (covers pilot + cheap-provider core Tier 1; premium-model core would
  need a ~$30-50 top-up, decided post-pilot from measured per-request cost). The
  stop-gate is now the actual remaining credit, tracked per RUNBOOK §8/§9.

## Scientific Contract (invariant)

The theorem pair is the analysis unit; samples/conditions/paraphrases are repeated
observations nested within a theorem, never independent theorems. The intervention
changes only the supplied informal proof, holding fixed: exact Lean declaration and
imports, model revision and decoding, system prompt (except the preregistered
preservation-vs-validity comparison), sample index/seed, resource limits, and all other
metadata. The primary claim is narrow: switching the supplied correct proof from A to B
changes the generated valid Lean proof toward the corresponding strategy more often than
theorem-only behavior predicts. No claims about human-like reasoning or full recovery of
model internals.

Benchmark inclusion (updated 2026-07-24): a core pair enters the frozen benchmark only
when (1) the exact Lean statement compiles in the pinned environment; (2) both informal
proofs are human-verified correct and complete enough to formalize; (3) strategies are
distinguishable by a blinded qualified annotator; (4) required/incompatible signatures
and acceptable refinements are recorded before model evaluation; (5) strategy-essential
vs. logically-necessary vs. explanatory steps are labeled; (6) paraphrases are drafted
and independently checked; (7) source/contamination metadata recorded. Pilot pairs
additionally require two compiling human-approved reference Lean proofs. Target mix
≈ ⅔ new/adapted, ⅓ familiar. Domains: elementary number/integer reasoning, finite
sums/sets, elementary algebra, divisibility, inequalities.

## Part 1 — PRE-SERVER (laptop)

### 1.1 Venue verification — DONE 2026-07-24
MATH-AI primary (Sept 25 AoE), VERICODEGEN fallback (Sept 10; decide by ~Sept 5).
Schedule anchor: all Part 2 work must leave ≥2 weeks before Sept 25 for annotation,
analysis, and writing.

### 1.2 Analysis agreement — DEFERRED with hard gate
Five decisions + worked examples live in docs/design-docs/analysis-decisions-pending.md.
They freeze after the pilot, before core results are inspected (T006). Second-annotator
recruitment tracked as T007.

### 1.3 Model slate & API agreement — categories fixed, IDs deferred
Four categories (Decision Log). How each category physically runs (vLLM
OpenAI-compatible serving covers categories 1-3 with ONE adapter; pipelines get
bespoke adapters; provisional model picks by GPU budget):
[docs/design-docs/model-slate-provisional.md](../../design-docs/model-slate-provisional.md).
Budget $500 ceiling, per-batch approval. Provider keys
and GPU expectations recorded when server access is confirmed (T008). Secret NAMES may
be listed in configs; secret VALUES never enter the repo, logs, or agent context
(stakes gate, coding-standard/README.md §4).

### 1.4 Benchmark curation — IN PROGRESS
Pipeline per pair (agent proposes, human approves, agent never self-approves):
discovery → extraction/drafting (license-safe adapted wording, cited sources) →
strategy metadata (labels, required/incompatible signatures, acceptable refinements,
step roles, dependency edges) → paraphrase drafting → Lean statement drafting (text
only, Status UNVERIFIED until server parse check) → human review.

Working conventions: candidates live in data/benchmark/candidates/, one numbered
Markdown file each, Status: draft/human_approved/rejected, Review notes section
mandatory. DISCOVERY-PROMPT.md is the reusable sourcing prompt for any agent (keeps the
exclusion list current — update it whenever candidates are added). Batches of 2-3 per
agent run. External agents (Codex) feed the same folder via the same template; the
Batch line records provenance. Comparison/dedup across agent outputs happens at human
review.

Current pool: 001-006 drafted (see files). Pilot needs 5 approved pairs spanning
multiple domains and proof-structure types; aim for ≤1 HIGH-contamination item in the
pilot.

### 1.5 Repo publication — PENDING (T004)
Create GitHub remote (name/visibility: user decision pending; provisional
recommendation private until release), push, confirm server can clone. After this,
GitHub is the single source of truth; laptop→server file copying is prohibited.

## Part 2 — SERVER (all code, all runs)

Every stage below follows coding-standard/: exploratory tier while prototyping,
promotion with tests + review agents before any component produces trusted output.
Stakes gate applies to all billed-API code (rate caps, spend caps, dry-run flags built
in at generation time).

**Ordered readiness gates (decision 2026-07-24 — pass strictly in order; a failed
gate sends work back, never forward):**

1. **Gate P (pairs)**: the human has approved exactly 5 pilot pairs from the candidate
   pool (Part 1.4). No server generation work references unapproved pairs.
2. **Gate S (statements + references)**: all 5 pilot pairs' Lean statements
   parse/elaborate in the pinned toolchain, and all 10 pilot reference proofs compile
   and pass the axiom audit with human approval (2.2).
3. **Gate C (components)**: every pipeline component — checker, dependency probe,
   harness, evaluation, and any judge/"approval" agent — has run against the 5
   approved pilot pairs via its fixtures and the S1-S5 Exit criteria, all green (2.3).
   No component is exercised for the first time during a paid run.
4. **Gate A (API smoke)**: the model-slate smoke test passes — every slate model does
   one end-to-end request on 1 theorem × 1 condition × 1 sample, cost recorded, slate
   frozen (2.4).
5. Only after P, S, C, A: the pilot smoke slice, then the full pilot (2.5). The same
   smoke-slice-first rule then repeats for the core run (2.6).

**Skip-don't-stall rule (decision 2026-07-24, user-directed):** human-gated items are
ordering constraints on PAID FULL RUNS and FROZEN artifacts — they are never a reason
for the agent to idle. When the agent reaches an unchecked human item (Gate P pilot-pair
approval, reference-proof approval in 2.2, the S3 metric HUMAN GATE, candidate-review
verdicts, T006/T007):

- Skip it, log "waiting on human: <item>" in the Progress section, and continue with
  every task not strictly dependent on it (all of S1-S5, fixtures, mock runs, drafts).
- Where the plan states a provisional/default choice, adopt it, mark it PROVISIONAL in
  the Decision Log, and proceed — but never promote a provisional choice into a frozen
  artifact (EXPERIMENT-SPEC.md, core manifest) without the human.
- Pipeline smoke testing does NOT wait for approved pilot pairs: run end-to-end against
  DRAFT candidate pairs and fixtures, labeling all such outputs `calibration/` —
  throwaway data that can never enter benchmark results.
- The dollar gate is the one thing this rule never bypasses: mock-adapter runs are free
  and unrestricted; any PAID request still requires an approvals/ record (RUNBOOK §8).
  The user may pre-place a small standing approval (e.g. max_usd 20, scope
  "smoke-tests") so API smoke tests also proceed unattended; without one, stay in mock
  mode and log the wait.

**Control plane**: how anything actually runs on the cluster — SLURM job scripts and
lifecycle, the run-state machine (planned→approved→submitted→running→terminal, in
state.json), worker locks against duplicate spend, provider rate limits,
machine-readable approval records under approvals/, the events.jsonl log vocabulary,
and the recovery-from-interruption procedure — is specified in
[docs/SERVER-HARNESS-RUNBOOK.md](../../SERVER-HARNESS-RUNBOOK.md) and is normative.
Module boundaries and trust zones: [docs/design-docs/ARCHITECTURE.md](../../design-docs/ARCHITECTURE.md).
Values freeze into [docs/design-docs/EXPERIMENT-SPEC.md](../../design-docs/EXPERIMENT-SPEC.md)
at each section's gate — check its Status header before trusting it.

### 2.1 Environment discovery
Read-only probes; write outputs/environment/server.json (OS, CPU, RAM, GPU count/
memory, storage quota, scheduler/partitions, container support, network policy,
toolchain versions, missing-secret NAMES). nvidia-smi/sinfo absence is recorded, not
fatal. Never print secret values. Do not create the repo inside an unrelated directory:
clone from GitHub into the user-designated path (RUNBOOK §2 has the full idempotent
setup transcript with expected outputs).

    uname -a && df -h . && python3 --version && uv --version && lake --version
    nvidia-smi; sinfo; git status --short

At this stage the `proof-faithfulness` CLI does not exist yet (it is built in S1) —
write outputs/environment/server.json by hand from the probe output, and copy the facts
into RUNBOOK §1. S1 later adds `env doctor` to regenerate it reproducibly. Crucially:
test outbound network FROM A COMPUTE NODE (`srun --pty curl -sI https://api.openai.com`)
— if compute nodes are offline, the generation-job placement in RUNBOOK §1 changes.

### 2.2 Scaffold + toolchain + statement verification
Python setup is reproducible, not bootstrap: pyproject.toml + uv.lock are already
committed (laptop-generated, 2026-07-24 — Python 3.12, 37 locked packages). Run
`uv sync --frozen --all-extras`; expect "Installed N packages" with zero resolution
work. If it errors about a missing/stale lockfile, the clone or the lockfile is wrong —
stop and report; NEVER run `uv lock` on the server (lockfile is laptop-owned).
Then pin Lean (4.15 provisional) in lean-toolchain; resolve exact Mathlib
tag+commit by compiling pilot references (record both; only the maintainer ever runs
lake update). Use the Mathlib cache command for the pinned release when available.
Then: parse/elaborate-check every curated Lean statement (flip UNVERIFIED → verified;
failures go back to curation as todo items); agent drafts the 10 pilot reference proofs,
compiles them, runs the axiom audit, and queues them for human approval.

Target layout (adapt minimally if the server repo differs; record mapping in Decision
Log): pyproject.toml, uv.lock, lean-toolchain, lakefile.toml, lake-manifest.json,
ProofFaithfulness/ (Audit.lean, Dependency.lean, Reference/Pilot/), configs/
(experiment/, models/), data/ (benchmark/, annotations/; raw/ gitignored), schemas/,
prompts/ (theorem_only_v1.txt, preservation_v1.txt, validity_only_v1.txt, repair_v1.txt),
experiments/, src/proof_faithfulness/ (cli.py, config.py, ids.py, schema.py,
artifacts.py, models/, generation/, lean/, evaluation/, reporting/), tests/
(unit/, integration/, fixtures/), outputs/ (gitignored).

### 2.3 Implementation stages S1-S5
Build in order; each stage has tests passing and a review pass before the next begins.
Every stage ends with an **Exit** line: the exact command and the observation that
means done — creating the files is never completion. None of S1-S5 spends money or
needs SLURM (login-node dev loop is fine); paid work starts at 2.4. Recovery from a
half-finished stage is always the same: `git status`, run that stage's Exit command,
finish whatever fails. Fixed choices (do not relitigate): Python 3.12, uv, Pydantic v2,
Typer, pytest, Ruff, Pyright, hatchling, src/ layout. Open choices are marked HUMAN
GATE where they occur. S1 also registers the `proof-faithfulness` console script in
pyproject.toml `[project.scripts]` (safe under the frozen lock — script entries do not
affect dependency resolution).

**S1 — Data contracts, IDs, artifact store.** Pydantic models + emitted JSON Schemas
for BenchmarkRecord (schema_version, theorem_id, domain, difficulty, source,
contamination, informal_statement, lean spec with statement hash/imports/toolchain,
exactly two proof_variants with signatures + steps + dependency edges + paraphrase,
split, status), GenerationRequest/Response, LeanCheckResult, StrategyJudgment,
StepAlignment, CounterfactualEvaluation. Reject duplicate IDs, dangling edges, cycles,
≠2 variants, missing hashes, identical A/B signatures. Deterministic request ID:

    request_id = sha256(schema_version | theorem_id | statement_hash | import_hash |
                        condition | proof_hash | prompt_hash | rendered_prompt_hash |
                        chat_template_hash | model_key | model_id | model_revision |
                        backend_config_hash | sampling_json | sample_index)

Content-addressed run directories (outputs/runs/<run_id>/ with manifest.json,
environment.json, requests.jsonl, responses/<request_id>/, lean/<request_id>/,
evaluations/*.jsonl, derived/*.parquet, reports/). Atomic writes (temp file +
same-filesystem rename), checksum verification, resume skips only verified terminal
artifacts, frozen runs immutable (child runs with parent_run_id instead).
Exit S1: `uv run pytest tests/unit -q` green (schema rejection cases, ID determinism —
same inputs twice → byte-identical request_id, artifact atomicity/immutability tests);
`uv run proof-faithfulness --help` lists the CLI; `uv run ruff check src tests` and
`uv run pyright` clean.

**S2 — Trusted Lean checker.** Canonical candidate assembly: fresh file from canonical
header + exact benchmark declaration; model supplies only the proof body (full
declarations accepted only when the normalized header hash matches exactly). Extractor
may strip Markdown fences and select one unambiguous block; it may NOT add imports,
repair syntax, or choose among multiple bodies. Execution: fresh process, no network,
120 s wall clock, 4 GB provisional memory limit, finite declared heartbeats. Reject
sorry/admit/sorryAx/custom axioms/unsafe/native trust bypasses; run #print axioms
(allow-list: propext, Classical.choice, Quot.sound; fail closed on unknown). Normalized
failure categories. Tests: valid, syntax-invalid, type-invalid, timeout, statement-
changed, sorry, custom-axiom, multi-block, allowed-classical.
Exit S2: `lake build` green; `uv run pytest tests/integration/test_lean_checker.py -q`
green with one fixture per category above, each asserting the exact normalized failure
category (not just pass/fail); the sorry and custom-axiom fixtures MUST be rejected.

**S3 — Dependency/utilization probe.** ProofFaithfulness/Dependency.lean metaprogram:
used-constant collection (Expr.getUsedConstants / ConstantInfo.getUsedConstantsAsSet),
binder/let traversal for explicit local facts, syntax-level tactic evidence for
preregistered signatures. Five fixtures: used induction structure; algebra/ring
normalization signature; explicit local lemma used; decorative unused local lemma;
automation bypassing supplied steps. Deletion tests validate used/unused calls.
HUMAN GATE: choose explicit-step utilization vs. full graph as the workshop metric.
If graph extraction is unreliable, freeze explicit utilization and move on — do not
delay the primary result.
Exit S3: `uv run pytest tests/integration/test_dependency_probe.py -q` green — all
five fixtures classified correctly, and the deletion test shows a used lemma's removal
breaks the proof while the decorative lemma's removal does not.

**S4 — Generation harness.** ModelAdapter protocol (capabilities: proof conditioning,
seeds, local inference, structured output, repair, cost reporting); adapters for
OpenAI-compatible APIs, local vLLM/HF, ProofBridge, ProofFlow (as reproducible);
prompt rendering with hashed templates; tiered condition matrix from configs;
plan/plan-check commands printing exact request counts per model and every
capability-based omission before any spend; caching, transport retries (same
request_id), resume; budget gates (cost ceiling halts new paid requests pending
approval). Request math for checking: T1 = 9/theorem (45 pilot, 270 core per
proof-conditioned model); T2 adds 6/theorem; theorem-only baselines = 3/theorem.
Defaults: temperature 0.2, top_p 1.0, max 8192 tokens — but a specialized model's
documented decoding recipe wins, recorded as a deviation. Repair track: ≤2 rounds,
exact compiler diagnostic returned, all versions stored, reported separately.
Exit S4: with a mock adapter and NO network, `uv run proof-faithfulness plan --tier 1
--split pilot` prints exactly 45 requests per proof-conditioned model (+15 theorem-only)
and a cost estimate; an end-to-end mock run writes a complete run directory (state.json,
events.jsonl, responses/) and re-running it is a verified no-op (resume skips all);
killing the mock run mid-flight and re-running completes it without duplicates. A paid
request without an approvals/ record must refuse (test asserts the refusal).

**S5 — Evaluation & annotation tooling.** Deterministic signature extraction; blinded
annotation bundle export (no model/prompt/condition/sample leakage — test this);
auxiliary LLM-judge with structured versioned output, blinded, never adjudicating its
own disagreements; import of independent human labels; disagreement queues; calibration
support (5-theorem calibration round, rubric revision, freeze); adjudication preserving
original labels; agreement statistics (raw, Gwet's AC1, Jaccard/label-wise F1, edge F1,
Krippendorff α; Cohen's κ as sensitivity). Fixtures: match A, match B, mixed,
unresolved, one-to-many alignment, implicit step, used/unused local fact, and a
library-lookup output (see Surprises 2026-07-24) coded per the frozen rubric.
Exit S5: `uv run pytest tests/unit/test_evaluation.py tests/integration/test_blinding.py
-q` green — the blinding test greps exported bundles and fails on ANY occurrence of
model name, condition key, prompt text, or sample index; agreement statistics reproduce
hand-computed values on a 10-item fixture to 4 decimals.

### 2.4 Model slate smoke tests → freeze
Weights download/storage/serving/sampling mechanics: RUNBOOK §3b (HF cache on project
storage, pinned commit hashes, vllm serve template, one-request-per-sample rule).
Per candidate model: minimal end-to-end run (1 theorem, 1 condition, 1 sample), record
model ID/revision/quantization/context/GPU/cost. Freeze the slate (≥1 per category)
with licenses and decoding configs. Record failed integrations rather than omitting.

### 2.5 Pilot (5 pairs)
Sequence: (1) smoke slice — 1-2 theorems through generate → lean check → inspect,
human reviews raw outputs; (2) full Tier 1 for all pilot pairs and all slate models;
(3) HUMAN CHECKPOINT: user reviews Tier-1 results; (4) Tier 2 on approval — Tier 2 is
**exploratory** (Decision Log 2026-07-24): it informs hypotheses and the T006 freeze,
never confirmatory claims;
(5) annotation calibration + pilot labels; (6) pilot gate. Gate criteria: references
compile; workflow end-to-end without manual edits; known faithful and unfaithful
fixtures classified correctly; used vs. unused local facts distinguished; rubric
manageable per annotators; projected core cost/runtime/human workload fits the Sept 25
deadline. On failure: diagnose the component, fix, version the pilot as exploratory —
never silently change benchmark definitions after seeing model-favorable results.

### 2.6 Freeze + core run (30 pairs)
Close T006 (analysis freeze) FIRST. Then freeze schemas, prompts, benchmark records,
model revisions, seeds, ambiguity rules, inclusion rules, and analysis code hashes in a
preregistration-style manifest that can recreate the exact request list. Core sequence:
smoke slice → human approval → Tier 1 full run with per-batch spend approval. The
precision-based expansion rule toward 50 pairs applies only as preregistered, never
conditioned on whether results look favorable. Tier 2+ on core: separate human
decision after Tier-1 results, recorded here — and permanently labeled exploratory in
the paper (confirmatory claims are Tier 1 only). Reference Lean proofs are added to a
core pair during annotation only when the pair is *disputed* per the mechanical rule
frozen at T006 as decision (g) in analysis-decisions-pending.md — never by informal
judgment after seeing results.

### 2.7 Robustness extension — POSTPONED (post-submission)
Corrupted/mismatched-proof extension deferred until after the MATH-AI submission.
Design notes retained in the old EXECPLAN §Conditions.

## Part 3 — POST-SERVER

### 3.1 Annotation
Blinded bundles → auxiliary LLM judge → two human annotators label independently
(humans see every automatic-vs-LLM disagreement, every uncertain case, plus a random
25% audit, minimum 10) → discussion → adjudication (originals preserved; unresolved
stays unresolved; third expert only if it materially affects the primary conclusion)
→ agreement report against the frozen threshold. Depends on T007.

### 3.2 Analysis
Exactly what the frozen analysis spec says, nothing more. Theorem-level metrics:
validity; conditional target match (descriptive); strict end-to-end pair
responsiveness; directional discrimination D_i = 0.5·[(M_i(A,A) − M_i(B,A)) +
(M_i(B,B) − M_i(A,B))]; proof-reliance lift L_i = 0.5·[(M_i(A,A) − M_i(0,A)) +
(M_i(B,B) − M_i(0,B))]; prompt-style effect (T2 vs T1); step coverage/utilization.
No composite score. Theorem-clustered bootstrap (whole-theorem resampling, fixed seed,
10,000 replicates unless the frozen spec says otherwise); mixed-effects logistic
strictly secondary with convergence/singularity checks; unresolved coded per frozen
rule with both bounds reported.

### 3.3 Reporting
All tables/figures/error analyses built from immutable run artifacts; reporting code
never triggers model calls; every reported cell traceable to theorem IDs and request
records. Paper: 4 pages + appendix, MATH-AI format, submitted by Sept 25 AoE.

### 3.4 Release
Publish gate per coding-standard/style/research.md §5 (pinned deps installable clean;
actual training/eval — here: generation/evaluation — code with real configs; README
results table with copy-paste reproduction commands verified from a fresh clone;
checkpoints N/A — release prompts, schemas, benchmark text where licensed, manifests,
aggregate results; data to a DOI repository or explicit note why not). Repo goes public
at camera-ready/acceptance (provisional). Release happens regardless of whether the
hypothesis was supported — a null result is a valid result.

### 3.5 Retrospective
Fill Outcomes & Retrospective below; move this file to docs/plans/completed/; update
PROGRESS.md and the coding-standard §8 process-reflection report (proposal-only).

## Testing and Acceptance Criteria (project-complete definition)

1. All CLI commands succeed on the target server from a clean clone.
2. Pilot gate passed; frozen manifest accounts for every requested and missing cell.
3. No raw datum or completed response overwritten during any resume.
4. Every accepted Lean output proves the exact statement under the allowed-axiom policy.
5. Annotations, disagreements, and adjudications are auditable with originals intact.
6. The report reconstructs every number from versioned data and code.
7. Tests, formatting, lint, types, and Lean builds pass (ruff format --check, ruff
   check, pyright, pytest -q, lake build).
8. A clean reproduction rebuilds the reported artifacts without hidden manual edits.

## Open Items (owners)

| ID | Item | Owner | Blocks |
|---|---|---|---|
| T006 | Freeze analysis decisions (a)-(e) + dispute rule (g) post-pilot | Tingxuan | Core run (2.6) |
| T007 | Second annotator (or preregistered fallback) | Tingxuan | Annotation (3.1) |
| T008 | Tillicum partitions/GPU/quota/network/secret delivery → RUNBOOK §1 | Tingxuan | Real-model smoke/freeze (2.4) |
| — | Candidate pool review (001-044) | Tingxuan | Gate P / pilot curation |
| — | VERICODEGEN fallback go/no-go | Tingxuan | ~Sept 5 |

## Outcomes & Retrospective

No implementation outcome yet. At completion record: date, final benchmark size, model
slate, Lean/Mathlib revisions, run-manifest IDs, primary estimates with intervals,
deviations from this plan, failed approaches, release location, and lessons. State
plainly whether the primary claim was supported, contradicted, or inconclusive.

## Revision Note

- 2026-07-24: Full rewrite of the 2026-07-22 EXECPLAN into pre-server/server/post-server
  structure after the interactive walkthrough: venue decided (MATH-AI), conditions
  tiered, pilot/core protocol with smoke slices and human checkpoints, reference-proof
  policy resolved (pilot-only), analysis decisions deferred with hard gate, curation
  conventions established, engineering rules delegated to coding-standard/. Old plans
  remain in docs/plans/active/ as reference pending formal retirement.
- 2026-07-24 (later): Incorporated the external Codex review via a grill session with
  the user. Why each change: the plan told the server to `uv sync --frozen` with no
  lockfile in the repo (bootstrap done on laptop, lockfile committed); the operational
  control plane existed only implicitly (now normative in docs/SERVER-HARNESS-RUNBOOK.md,
  SLURM confirmed); the planning standard lived outside the repo and would not survive
  the clone (copied to docs/plans/PLANS.md); S1-S5 lacked observable exit criteria
  (added Run/Expect lines); Tier 2's post-hoc trigger made it silently exploratory
  (now labeled explicitly); "disputed core case" was an undefined judgment call (now
  decision (g), frozen at T006); ARCHITECTURE.md + gated EXPERIMENT-SPEC.md stub added.
  Old plans still retire at T009 per user instruction (leave in place until sign-off).
