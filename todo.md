# todo.md

Priority tags per [coding-standard/README.md](coding-standard/README.md) §5:
P0 = stakes-gate/security · P1 = bugs · P2 = design · P3 = deferrable.
Every entry gets an ID (T001, T002, ...) so in-code TODOs can reference it.

## Open

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
- [ ] T012 (P0) Frontier API key placement — the user provides the key to the server
      agent only after T016 proof processing and only for an approval-bound API smoke.
      S4 transports and T011's paid-request permit/refusal tests are complete. Keep the
      value outside the repo, logs, and agent context; inject it by environment variable
      at job submission under RUNBOOK §3. The provider name and key remain pending; do
      not request either at this checkpoint.
- [ ] T007 (P2) Recruit a second qualified annotator (or explicitly preregister a
      single-annotator + LLM-judge fallback). Blocks the annotation phase.
      See analysis-decisions-pending.md §(f).
- [ ] T015 (P3) Resolve the repository's 100-column Ruff setting versus the coding
      standard's mandatory 80-column rule in a dedicated formatting-policy change; do
      not mix a whole-tree reformat into behavioral pipeline work.
- [ ] T016 (P0) Pending human input: process the generated Lean reference proofs for
      pilot candidates 001/033/036/040/041 as they arrive. Run each through the S2
      trusted checker and S3 dependency probe and report compilation, normalized failure
      category, axiom audit, route, and banned-lemma hits. Do not change human-owned
      faithfulness approvals, candidate Status fields, or the proposed Gate-P slate.
- [ ] T017 (P1) Deferred deep review — S2/S3 trusted checking and dependency analysis.
      **Status:** pending. **Scope/stage/files:** S2-S3;
      `ProofFaithfulness/{Audit,Dependency}.lean`, `src/proof_faithfulness/lean/**`, and
      their fixtures/integration tests. **Standards:** full
      `coding-standard/CODE_REVIEW.md` plus `coding-standard/style/research.md` pass.
      **Known risks/questions:** sandbox portability, diagnostic-marker provenance,
      parser/category normalization, and regressions around theorem-parameter-type lets
      versus candidate-introduced local facts. **Prerequisites:** stable pilot Lean
      imports and representative T016 proofs. **Risk priority:** P1
      correctness/trust-boundary review.
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
      label schema, annotation protocol, and representative export bundles. **Risk
      priority:** P1 research-integrity review before human annotation or paper analysis.
- [ ] T020 (P1) Deferred deep review — cross-stage reproducibility and recovery.
      **Status:** pending. **Scope/stage/files:** S1-S5 integration; schemas, request IDs,
      manifests, artifact/checksum stores, resume/repair lineage, CLI entrypoints, and
      cross-stage tests. **Standards:** full `coding-standard/CODE_REVIEW.md` plus
      `coding-standard/style/research.md` pass. **Known risks/questions:** identity drift
      across schema versions, partial-write recovery, stale checksums, environment capture,
      and clean-clone/second-host reproducibility. **Prerequisites:** individual stage
      contracts frozen and an integration fixture run available on both intended hosts.
      **Risk priority:** P1 because silent lineage drift can invalidate experiment results.

## Pending Human Inputs

1. **Load-bearing artifact declarations (T001):** the owner declares the benchmark-pair,
   Lean-statement, and strategy-prompt artifacts in `PROJECT_ARTIFACTS.md`.
2. **Pilot candidate and reference approval:** humans review the proposed pilot-5 and
   retain ownership of Gate-P/Gate-S approval, candidate Status fields, and freezes.
3. **Analysis and S3 metric freeze (T006):** humans choose the workshop estimand and
   explicit-step versus full-graph utilization before inspecting core-run results.
4. **Annotation staffing (T007):** recruit the second qualified annotator or explicitly
   preregister the documented fallback.
5. **Process the generated Lean reference proofs for 001/033/036/040/041 (T016):**
   generated Lean proofs may be processed incrementally through S2/S3; results are
   reported without changing human-owned approval or Status fields.
6. **Obtain the frontier API key and run the approved API smoke slice (T012):** after
   item 5, receive the key only via the server secret-delivery path and run the API smoke
   only when the user has placed a matching machine-readable approval record.

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
