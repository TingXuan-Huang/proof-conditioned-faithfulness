# todo.md

Priority tags per [coding-standard/README.md](coding-standard/README.md) §5:
P0 = stakes-gate/security · P1 = bugs · P2 = design · P3 = deferrable.
Every entry gets an ID (T001, T002, ...) so in-code TODOs can reference it.

## Open

- [ ] T022 (P0) Human review and freeze of the real-backend model slate. Review
      `docs/REAL-BACKEND-COMPATIBILITY-REPORT.md`; choose final `ready`/`fallback`
      backends; decide whether DeepSeek's multi-block output needs a prompt/contract
      change; and decide whether to replace, patch, or exclude ProofBridge/ProofFlow.
      Compatibility testing is complete, but no model-slate, Gate A, pilot, or core
      approval is implied. **Status:** pending human review.
- [ ] T023 (P1) Human incident and publication review. Read
      `docs/CLUSTER-EXPERIMENT-INCIDENTS.md`, validate the failure classifications and
      accepted operational limits, confirm the exposed Meta credential is revoked,
      inspect all local commits/diffs after an authenticated `git fetch`, rerun the
      secret scan, and push only from the owner's authenticated session. This review
      does not close any scientific or readiness gate. **Status:** pending.
- [ ] T021 (P2) Complete the human manual review and decision checklist in
      `docs/HUMAN-REVIEW-TODO.md`. It covers interactive reproduction, trusted Lean
      checking, model/prover execution, paid API safeguards, incident acceptance,
      authenticated publication, blinding/annotation, observed errors, and every
      architecture/scientific question that must be human gated. All checkboxes are
      human-owned; agents may add evidence but never mark approval.

- [ ] T001 (P2) Fill out `coding-standard/PROJECT_ARTIFACTS.md` — declare this project's
      load-bearing artifacts (human-owned; candidates per HUMAN_PLAN: the benchmark
      pair data, the Lean statement translations, the strategy-labeling prompts).
- [ ] T002 (P2) Add LICENSE and CITATION files. The active plan's uv + hatchling setup
      supersedes the generic PROJECT_SETUP.md conda + setup.py defaults; the committed
      `uv.lock` and editable uv environment are already operational.
- [ ] T006 (P2) Freeze the five analysis decisions (primary estimand, sample pairing,
      ambiguity coding, uncertainty method, agreement threshold) — full explanations and
      examples in docs/design-docs/analysis-decisions-pending.md. Deferred by design:
      decide after the pilot run, but **hard gate: frozen before core-run results are
      inspected**.
- [ ] T008 (P2) Finish account-specific server discovery. Discovered and recorded in
      `docs/SERVER-HARNESS-RUNBOOK.md` §1: Klone CPU/GPU allocations, L40/L40S count and
      48 GB VRAM, project quota and purge policy, and working compute-node egress;
      Tillicum's public H200 141 GB topology, QoS limits, storage/purge policy, and
      $0.90/GPU-hour rate. Still undiscoverable without human/account access: Tillicum
      allocation and credit attachment/expiration, direct compute-node egress, secret
      delivery, and the exact frontier-provider name. Keep these open for the 2.4 slate
      freeze; do not infer them.
- [ ] T010 (P3) Rerun the LOW-CONTAMINATION discovery round — the round-3 agent
      hunting deliberately obscure A/B pairs died on a session usage limit
      (2026-07-24, resets 7pm PT) with zero results. Why it matters: the pool of 44
      runs famous-heavy (~1/3 HIGH-risk) against the ⅔-new/adapted target, so fresh
      LOW/LOW-MED pairs are the scarcest resource for the final 30. How: launch 1-3
      Opus agents with the prompt in data/benchmark/candidates/DISCOVERY-PROMPT.md,
      objective "minimize contamination" (hunt problem-set corners, regional
      olympiad training, second-tier identities; agent should reject its own HIGH
      finds), exclusion list 1-43 + NOTES-library-collapse-catalog.md. File keepers
      as 045+. Optional — do after (or during) the human review pass reveals which
      domains still need low-contamination fills.
- [ ] T012 (P0) Production frontier API credential and approval. One Meta Muse Spark
      testing-only request has now run through the matching approval, persisted at
      `$0.008082`, and resumed without a duplicate. It is not a frontier scientific
      result. GPT-5.6 Terra received no request and still requires an independently
      reviewed provider contract, rotated credential, manifest-bound approval, and
      explicit human authorization. A credential value was pasted into chat; revoke it
      in the provider dashboard and use only a fresh environment-injected value later.
      S4 preflight and T011 refusal/spend controls are complete. **Status:** pending.
- [ ] T007 (P2) Recruit a second qualified annotator (or explicitly preregister a
      single-annotator + LLM-judge fallback). The owner reports that a second annotator
      is secured; onboarding, conflict/independence confirmation, rubric training, and
      calibration remain human-owned before annotation. See
      analysis-decisions-pending.md §(f). **Status:** pending human confirmation.
- [ ] T015 (P3) Resolve the repository's 100-column Ruff setting versus the coding
      standard's mandatory 80-column rule in a dedicated formatting-policy change; do
      not mix a whole-tree reformat into behavioral pipeline work.
- [ ] T016 (P0) Process generated Lean reference proofs for pilot candidates
      001/033/036/040/041. All ten submitted routes were compile-screened by extended
      SLURM job `37700033`: `036-A` compiled without `sorry` and reported only allowed
      axioms (`propext`, `Quot.sound`); the other nine produced persisted Lean compile
      diagnostics and are skipped under the prototype policy rather than repaired.
      `033-A`, `041-A`, and `041-B` additionally contain `sorry`. Trusted node-local job
      `37724510` accepted the exact `036-A` statement/body with allowed axioms and no
      prohibited tokens, persisted S3 successfully, and passed every artifact checksum.
      Its provisional S3 classification is `automation_bypass`; humans must interpret
      whether brief-permitted side-goal `omega` still realizes Route A. The mechanical
      scan found one contextual brief-ban hit: `041-B` uses `decide`; no contextual hit
      was recorded for the other nine routes. See `docs/T016-REFERENCE-PROOF-REPORT.md`.
      **Remaining status is human-owned:** approve/reject `036-A`, decide whether to
      repair/replace the nine failures, and update Gate S/candidate Status only through
      human review. The item stays open; agent processing does not approve it.
- [ ] T017 (P1) Deferred deep review — S2/S3 trusted checking and dependency analysis.
      **Status:** pending. **Scope/stage/files:** S2-S3;
      `ProofFaithfulness/{Audit,Dependency}.lean`, `src/proof_faithfulness/lean/**`, and
      their fixtures/integration tests. **Standards:** full
      `coding-standard/CODE_REVIEW.md` plus `coding-standard/style/research.md` pass.
      **Known risks/questions:** sandbox portability, diagnostic-marker provenance,
      parser/category normalization, GPFS metadata stalls, node-local archive integrity
      and cleanup, resource-signal classification, warm-up effectiveness across hosts,
      enforcement of 8 GiB and separate 1,200/600-second limits, and regressions around
      lets versus candidate-introduced local facts. **Prerequisites:** stable pilot Lean
      imports, representative T016 proofs, and a human-frozen S3 utilization metric.
      **Human/code boundary:** humans define the A/B strategy signatures, decide what
      constitutes meaningful strategy use, and resolve ambiguous proofs. The deep code
      review only verifies that dependency evidence, deletion tests, and normalized
      classifications implement those decisions faithfully; it cannot approve
      faithfulness. **Risk priority:** P1 correctness/trust-boundary review.
- [ ] T018 (P0) Deferred deep review — S4 generation, transport, and paid-spend controls.
      **Status:** pending. **Scope/stage/files:** S4; `src/proof_faithfulness/generation/**`,
      `src/proof_faithfulness/models/**`, CLI/configs, and generation tests.
      **Standards:** full `coding-standard/CODE_REVIEW.md` plus
      `coding-standard/style/research.md` pass. **Known risks/questions:** provider-specific
      pre-acceptance retry classification, crash windows, cross-run duplicate inference,
      approval/manifest binding, concurrent ledger/lock recovery, optional batch
      transport, and the production request-order/randomization policy.
      **Prerequisites:** finalized request manifest and provider configuration; any live
      transport check additionally requires T012 and a human-owned matching approval.
      **Risk priority:** P0 because mistakes can duplicate paid requests or exceed
      authorization.
- [ ] T019 (P1) Deferred deep review — S5 evaluation, annotation, and blinding.
      **Status:** pending. **Scope/stage/files:** S5;
      `src/proof_faithfulness/evaluation/**` and evaluation/blinding fixtures and tests.
      **Standards:** full `coding-standard/CODE_REVIEW.md` plus
      `coding-standard/style/research.md` pass. **Known risks/questions:** encoded or
      indirect identity leakage, conservative sample-index false positives, incomplete
      packet provenance, and agreement-statistic edge cases. **Prerequisites:** frozen
      label schema, human-owned annotation rubric/protocol, and representative pilot
      export bundles. **Human/code boundary:** humans independently label strategy use,
      adjudicate disagreements, and decide whether evidence is scientifically meaningful.
      The deep code review verifies blinding, label/proof association, preservation of
      originals, queues, and agreement calculations; it does not substitute for human
      annotation. **Risk priority:** P1 research-integrity review after the rubric is
      stable and before core annotation or paper analysis.
- [ ] T020 (P1) Deferred deep review — cross-stage reproducibility and recovery.
      **Status:** pending. **Scope/stage/files:** S1-S5 integration; schemas, request IDs,
      manifests, artifact/checksum stores, resume/repair lineage, CLI entrypoints, and
      cross-stage tests. **Standards:** full `coding-standard/CODE_REVIEW.md` plus
      `coding-standard/style/research.md` pass. **Known risks/questions:** identity drift
      across schema versions, partial-write recovery, stale checksums, environment capture,
      node-local versus shared-path equivalence, and clean-clone/second-host
      reproducibility. **Prerequisites:** individual stage contracts frozen and a
      terminal node-local integration fixture available on both intended hosts.
      **Risk priority:** P1 because silent lineage drift can invalidate experiment results.

## Pending Human Inputs

The actionable review order and exact manual commands are maintained in
`docs/HUMAN-REVIEW-TODO.md` (T021). The summary below remains the compact intake queue.

1. **Load-bearing artifact declarations (T001):** the owner declares the benchmark-pair,
   Lean-statement, and strategy-prompt artifacts in `PROJECT_ARTIFACTS.md`.
2. **Pilot candidate and reference approval:** humans review the proposed pilot-5 and
   retain ownership of Gate-P/Gate-S approval, candidate Status fields, and freezes.
3. **Analysis and S3 metric freeze (T006):** humans choose the workshop estimand and
   explicit-step versus full-graph utilization before inspecting core-run results.
   Humans also own the interpretation of route signatures and ambiguous strategy use;
   the T017 code review follows the freeze and checks only that the implementation
   measures the chosen definition correctly.
4. **Annotation staffing (T007):** recruit the second qualified annotator or explicitly
   preregister the documented fallback. The owner reports the second annotator is
   secured; humans still confirm onboarding/independence, freeze the rubric, label
   proofs, and adjudicate disagreements. T019 follows representative pilot exports.
5. **Human disposition of generated Lean references (T016):** agent compilation,
   trusted `036-A` S2/S3, and the banned-lemma report are complete. Humans retain
   approval and Status ownership, must interpret `036-A`, and must decide whether Gate S
   needs repaired or replacement references for the nine failed routes.
6. **Rotate/configure the later frontier credential (T012):** the Meta testing-only
   smoke is complete. Revoke the chat-exposed key. GPT-5.6 Terra remains uncalled and
   needs its own provider-contract review, fresh environment-delivered key, exact
   manifest approval, and explicit human authorization before any later request.

## Done

- [x] T011 (P0) 2026-07-25 — Implemented the generation-layer paid-request permit and
      refusal path. Each human approval binds exactly one run to `requests_sha256`,
      `request_count`, and `max_usd`; the harness atomically reserves worst-case spend,
      issues a typed approval-bound permit, verifies it immediately before transport,
      and settles actual cost in a checksummed `budget.json` ledger. Per-run and absolute
      $500 aggregate ceilings, cross-run inference deduplication, fail-closed ambiguous
      paid retries, and empty-`approvals/` refusal are tested. No paid API request was made.
- [x] T014 (P0) 2026-07-25 — Reviewed overwrite-capable CLI paths for the stakes gate.
      Schema export refuses changed files without explicit `--force`, writes atomically,
      and has overwrite tests; model inspection performs no writes or network access and
      never reads secret values.
- [x] T013 (P1) 2026-07-25 — Recorded the hand-computed model-cost sanity check:
      `(10 input × $2 + 4 output × $4) / 1,000,000 = $0.000036`; the unit test matches.

- [x] T003 (P2) 2026-07-24 — Pinned Lean 4.15.0 and Mathlib tag v4.15.0 at commit
      9837ca9d65d9de6fad1ef4381750ca688774e608; cache retrieval and `lake build` passed
      on the Klone dev/test host.
- [x] T004 (P3) 2026-07-24 — GitHub remote added and pushed:
      https://github.com/TingXuan-Huang/proof-conditioned-faithfulness.git (commit f79f0ac).
      GitHub is now the single source of truth; laptop→server file copying prohibited.
- [x] T009 (P2) 2026-07-24 — Old plans banner-retired to docs/plans/completed/;
      all pending work committed. PLAN.md is the sole active plan.

- [x] T005 (P3) 2026-07-24 — Venue verified: **MATH-AI @ NeurIPS 2026 (Atlanta)** is the
      primary target — deadline Sept 25, 2026 AoE, notification Oct 19, 4 pages +
      unlimited refs/appendix, non-archival (https://mathai-2026.github.io/cfp).
      Fallback: VERICODEGEN (deadline Sept 10, Lean/autoformalization explicitly in
      scope, https://vericodegen.github.io/) — fallback decision needed by ~Sept 5.
