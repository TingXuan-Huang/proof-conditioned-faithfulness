> **SUPERSEDED (2026-07-24).** This plan is retired (todo T009). The single
> controlling plan is [../active/PLAN.md](../active/PLAN.md). This file is kept as
> historical reference only — do not execute from it.

# Joint Agent–Human Plan: Curating 30 A/B Proof-Strategy Examples

Last updated: 2026-07-23


## 1. Purpose

This plan connects the coding-agent work in proof-conditioned-faithfulness-EXECPLAN.md with the scientific and annotation work in proof-conditioned-faithfulness-HUMAN_PLAN.md.

The goal is to produce 30 human-approved examples. Every example has:

1. one mathematical theorem;
2. an informal proof using strategy A;
3. an informal proof using a genuinely different strategy B;
4. traceable evidence that both strategies come from reliable, human-authored mathematical sources;
5. an agent-written, machine-processable summary of both strategies;
6. an agent-translated Lean theorem statement with fixed imports and toolchain metadata; and
7. recorded human decisions about source quality, mathematical correctness, same-theorem equivalence, strategy distinctness, and Lean-statement fidelity.

The agent does the expensive discovery, extraction, normalization, citation, and first-pass Lean translation. Humans make the trust decisions. An agent may propose that a pair is ready, but it may never mark its own proposal human-approved.


## 2. Important Scope Boundary

- [x] A and B must both be real, correct informal proof strategies supported by human-authored sources.
- [x] The agent must translate the shared theorem statement into Lean.
- [x] The Lean statement must parse and elaborate as a proposition in the pinned Lean/Mathlib environment.
- [x] A Lean proof is not required to complete this 30-pair curation stage.
- [x] The source proofs do not need existing Lean translations.
- [x] Full copyrighted textbook proofs should not be copied into the dataset unless their license clearly permits redistribution.
- [x] Human approval is required before a pair enters the curated set.

The earlier ExecPlan and Human Plan currently require compiling reference Lean proofs before the final benchmark is frozen. This new plan adopts the newer instruction that reference Lean proofs are not required for the 30-pair sourcing and review stage. Before the core experiment is frozen, the project lead must synchronize the older plans by either removing that reference-proof requirement or retaining it as a later optional validation step. Until that edit is made, curation_approved and benchmark_frozen are intentionally different statuses.


## 3. Definition of the Final Curation Deliverable

The curation work is complete when:

- [ ] Exactly 30 pairs have status curation_approved.
- [ ] Every pair has one normalized theorem statement and exactly two proof variants, A and B.
- [ ] Both variants have reliable source records and precise source locators.
- [ ] Both proof summaries are faithful paraphrases or licensed extracts, not agent-invented proofs.
- [ ] A and B prove the same theorem under the same assumptions.
- [ ] A and B differ in mathematical strategy, not only wording, notation, or Lean tactics.
- [ ] Every Lean statement parses and elaborates as a proposition under the recorded imports and pinned toolchain.
- [ ] Every Lean statement has a stable hash and passes automated schema checks.
- [ ] A qualified human has approved source quality and mathematical correctness.
- [ ] A qualified Lean/math reviewer has approved informal-to-Lean statement fidelity.
- [ ] Every rejection and revision remains in an auditable log.
- [ ] Copyright and redistribution status is recorded for every source.
- [ ] The 30 approved records can be loaded without manual cleanup by the benchmark runner.


## 4. Roles and Authority

### Sourcing agent

- [ ] Search for candidate theorems with two independently documented proof strategies.
- [ ] Open and inspect the actual source, not only a search-result snippet.
- [ ] Verify author, publication, edition, page/section, URL, access date, and license information.
- [ ] Extract the theorem, assumptions, and both proof strategies.
- [ ] Paraphrase proof steps unless verbatim reuse is licensed and necessary.
- [ ] Record direct quotes separately and keep them short.
- [ ] Reject weak or anonymous sources instead of filling gaps from model memory.
- [ ] Create candidate JSONL records and source-registry entries.
- [ ] Draft the Lean theorem statement and run automated statement checks.
- [ ] Respond to human change requests with a new record version.
- [ ] Never mark source_quality_approved, math_approved, lean_equivalence_approved, or curation_approved.

### Human mathematical reviewer

- [ ] Open the cited source pages or sections.
- [ ] Confirm that each source is genuinely human-authored and sufficiently reliable.
- [ ] Confirm that proof A and proof B are mathematically correct.
- [ ] Confirm that both proofs establish the same theorem under the same assumptions.
- [ ] Confirm that their difference is strategic rather than cosmetic.
- [ ] Approve, request changes, or reject with a written reason.

### Human Lean/math reviewer

- [ ] Compare the informal theorem and assumptions against the proposed Lean statement.
- [ ] Check domains, quantifiers, types, side conditions, coercions, finiteness assumptions, and edge cases.
- [ ] Review the fixed imports and any Mathlib definitions that change interpretation.
- [ ] Confirm that automated elaboration checked the proposition rather than silently proving a weaker statement.
- [ ] Approve, request changes, or reject with a written reason.

### Project lead

- [ ] Set domain and strategy-diversity targets.
- [ ] Resolve disputed reviews.
- [ ] Approve source-policy exceptions.
- [ ] Freeze schema and review-rubric versions.
- [ ] Decide how the older reference-Lean-proof requirement is synchronized.
- [ ] Freeze the final 30-pair set.


## 5. Reliable-Source Policy

### Preferred sources

Use sources in roughly this order:

1. published mathematics textbooks with named authors, edition metadata, publisher, and page or theorem number;
2. peer-reviewed journal or conference expositions;
3. named university lecture notes, course notes, or problem sets hosted on an institutional domain;
4. official publications from mathematical societies or recognized educational organizations;
5. a named mathematician's professional website or expository article when authorship and credentials can be verified.

Proof A and proof B may come from the same source if it explicitly presents two proofs. They may also come from separate sources, but the agent must show that the theorem statements and assumptions are equivalent.

### Supplementary-only sources

MathOverflow, Mathematics Stack Exchange, personal blogs, and collaborative encyclopedias may help discovery. They are acceptable as primary evidence only when the author is named or otherwise credibly attributable, the reasoning is complete enough to review, and an independent reliable source confirms the theorem. Anonymous posts, unattributed wiki text, and discussion comments are not sufficient on their own.

### Excluded sources

- [ ] Do not use AI-generated pages or proofs as evidence.
- [ ] Do not use search-result snippets as evidence.
- [ ] Do not use SEO content farms, anonymous solution dumps, or pages with no stable authorship.
- [ ] Do not use a model's remembered proof unless a human-authored source is subsequently found and inspected.
- [ ] Do not cite a source that merely states the theorem but does not support the claimed proof strategy.
- [ ] Do not use a source when assumptions or notation cannot be reconstructed confidently.
- [ ] Do not claim that a source has two strategies when only one appears in the inspected material.

### Copyright and source preservation

- [ ] Store bibliographic metadata and exact locators for every source.
- [ ] Store agent-written proof summaries and structured steps by default.
- [ ] Store only short quotations needed to support interpretation.
- [ ] Store a full proof verbatim only when it is public domain, openly licensed for redistribution, or explicit permission exists.
- [ ] Record license, terms, and redistribution_allowed as true, false, or unknown.
- [ ] Keep non-redistributable source snapshots outside the public repository.
- [ ] Store a checksum for any private snapshot so reviewers can verify that they saw the same version.
- [ ] Preserve access dates and stable archive links when legally and technically appropriate.


## 6. Scale, Diversity, and Batching

The target is 30 approved pairs, not merely 30 discovered candidates. Because some candidates will fail source, equivalence, strategy, or Lean review, the agent should initially discover 45 to 60 candidates.

Work in batches of five approved pairs. Never place more than ten unresolved candidates in the human review queue at once.

Provisional domain targets are six approved pairs in each of five groups:

1. natural numbers and integers;
2. divisibility and elementary number theory;
3. elementary algebra and identities;
4. finite sums and elementary combinatorics; and
5. finite sets and inequalities.

These are diversity targets, not permission to accept weak pairs. The project lead may rebalance them with a dated rationale.

Across the collection, seek multiple kinds of A/B contrast:

- [ ] induction versus a direct or closed-form argument;
- [ ] algebraic manipulation versus a combinatorial interpretation;
- [ ] contradiction or contrapositive versus a direct proof;
- [ ] constructive witness versus an existence argument;
- [ ] invariant or extremal reasoning versus local calculation;
- [ ] counting the same set in two ways;
- [ ] factorization or divisibility decomposition versus modular reasoning;
- [ ] inequality normalization versus an order-theoretic argument.

Do not force a theorem into a contrast that its sources do not genuinely demonstrate.


## 7. End-to-End Workflow

### Stage 0 — freeze the curation rubric

- [ ] Define schema version 1.
- [ ] Define the reliable-source rubric.
- [ ] Define strategy-family labels and examples.
- [ ] Define same-theorem equivalence rules.
- [ ] Define Lean-statement review questions.
- [ ] Define rejection reasons and status transitions.
- [ ] Calibrate the process on two candidate pairs before scaling.

Agent output: schema, empty templates, and two sample records.

Human output: approved rubric version or requested revisions.

Exit condition: both human reviewers can apply the rubric consistently to the calibration records.

### Stage 1 — broad candidate discovery

- [ ] Search named textbooks, papers, institutional notes, and mathematician-authored expositions.
- [ ] Log each query, repository, catalog, or site searched.
- [ ] Record candidates even when later rejected, to avoid duplicate work.
- [ ] Prefer explicit “two proofs” examples, then match proofs from separate sources carefully.
- [ ] Collect 45 to 60 candidates before assuming 30 will survive.
- [ ] Assign stable pair IDs immediately.

Agent output: discovery_queue.jsonl and rejection_log.jsonl.

Human output: none required for every raw discovery; the project lead may redirect domains or source types after each batch summary.

Exit condition: the queue has enough source-backed candidates to begin batches without relying on model memory.

### Stage 2 — source verification

- [ ] Open the full source.
- [ ] Record complete citation metadata.
- [ ] Verify the claimed proof appears at the recorded locator.
- [ ] Verify named human authorship or editorial provenance.
- [ ] Record license and redistribution status.
- [ ] Create a source checksum or stable locator.
- [ ] Mark weak evidence for rejection rather than repair it through inference.

Agent output: source_registry.jsonl and source-verification evidence.

Human output: spot-check source identity before extraction begins; fully review sources at the approval stage.

Exit condition: both A and B have source_verified evidence.

### Stage 3 — theorem and proof extraction

- [ ] Extract the theorem's variables, domains, assumptions, conclusion, and notation.
- [ ] Normalize the shared theorem in plain mathematical language.
- [ ] Create a source-faithful paraphrase of proof A.
- [ ] Create a source-faithful paraphrase of proof B.
- [ ] Split each proof into ordered mathematical steps.
- [ ] Record dependencies among steps.
- [ ] Label the strategy family and theorem-specific realization.
- [ ] Record required and incompatible strategy signatures.
- [ ] Explain why A and B prove the same theorem.
- [ ] Explain why A and B are strategically distinct.
- [ ] Flag every inferred bridge that is not explicit in the source.

Agent output: a versioned CandidatePair record.

Human output: none yet, unless the agent identifies a mathematical ambiguity requiring early review.

Exit condition: schema validation passes and every extracted claim has a source locator or an explicit inference flag.

### Stage 4 — Lean statement translation

- [ ] Choose Mathlib types and definitions that match the informal domains.
- [ ] Translate every variable, quantifier, assumption, and conclusion.
- [ ] Use the fixed project imports unless a justified import is added.
- [ ] Store the theorem type separately from any proof body.
- [ ] Generate a statement-check wrapper that defines the proposition without proving it.
- [ ] Run Lean parsing and elaboration on the wrapper.
- [ ] Record exact Lean version, Mathlib commit, imports, diagnostics, and statement hash.
- [ ] Run simple boundary-instance checks when they can expose a translation mistake.
- [ ] Write a plain-language equivalence note for the human reviewer.

Agent output: lean_statement, lean_check metadata, and the exact generated check file.

Human output: none until the review packet is assembled.

Exit condition: the proposition parses and elaborates with no sorry, admit, axiom, or proof placeholder.

### Stage 5 — review-packet assembly

- [ ] Include the normalized theorem.
- [ ] Include proof A and B summaries and structured steps.
- [ ] Include direct source links and precise page/section locators.
- [ ] Include source-quality evidence and license status.
- [ ] Include same-theorem and strategy-distinctness explanations.
- [ ] Include the proposed Lean statement, imports, and equivalence notes.
- [ ] Include automated schema and Lean-check results.
- [ ] Remove model confidence scores that could anchor human judgment.
- [ ] Present reviewers with the source material, not only the agent's summary.

Agent output: one immutable review packet per record version.

Human output: independent review records.

Exit condition: the packet contains everything needed for a reviewer to approve or reject without asking the agent where a claim came from.

### Stage 6 — human review and revision

- [ ] Mathematical reviewer checks source reliability.
- [ ] Mathematical reviewer checks correctness and completeness of A and B.
- [ ] Mathematical reviewer checks same-theorem equivalence.
- [ ] Mathematical reviewer checks strategy distinctness.
- [ ] Lean/math reviewer checks the informal-to-Lean statement.
- [ ] Each reviewer chooses approve, changes_requested, or reject.
- [ ] Each reviewer writes a reason for rejection or requested changes.
- [ ] Agent creates a new version rather than overwriting the reviewed record.
- [ ] Reviewers confirm revisions before approval.

Agent output: revised records and a response-to-review log.

Human output: signed, version-specific review records.

Exit condition: both required approvals refer to the same record version.

### Stage 7 — promotion and freeze

- [ ] Promote only fully approved records to curated_pairs.jsonl.
- [ ] Re-run schema and Lean statement checks over the complete set.
- [ ] Check IDs, hashes, duplicate theorems, source reuse, domain balance, and strategy balance.
- [ ] Confirm exactly 30 approved records.
- [ ] Freeze source registry, schema, rubric, and record hashes.
- [ ] Export the prover-facing dataset without private source snapshots.
- [ ] Record every excluded candidate and reason.
- [ ] Resolve the reference-Lean-proof policy mismatch with the older plans.

Agent output: frozen curation manifest and machine-readable dataset.

Human output: project-lead freeze approval.

Exit condition: the benchmark runner can load all 30 records, and no record relies on an unapproved or unavailable source claim.


## 8. Machine-Processable Files

The implementation should create these files:

    data/curation/source_registry.jsonl
    data/curation/discovery_queue.jsonl
    data/curation/candidate_pairs.jsonl
    data/curation/human_reviews.jsonl
    data/curation/rejection_log.jsonl
    data/curation/curated_pairs.jsonl
    schemas/source_record.schema.json
    schemas/candidate_pair.schema.json
    schemas/human_review.schema.json
    outputs/curation/review_packets/
    outputs/curation/lean_statement_checks/
    outputs/curation/frozen_manifest.json

Raw source snapshots that cannot be redistributed live in approved private research storage, not in the public Git repository. The public source registry keeps citations, locators, license status, and checksums.


## 9. Source Record Schema

Each source_registry.jsonl record should contain:

    schema_version: string
    source_id: string
    source_type: textbook | paper | university_notes | society_site |
                 mathematician_site | forum | encyclopedia | other
    title: string
    authors:
      - name: string
        affiliation_or_credentials: string | null
        authorship_evidence_url: string | null
    publisher_or_institution: string | null
    edition: string | null
    publication_year: integer | null
    isbn: string | null
    doi: string | null
    url: string | null
    access_date: date | null
    locator:
      page: string | null
      chapter: string | null
      section: string | null
      theorem_or_example: string | null
    human_authorship_verified: boolean
    reliability_tier: preferred | supplementary | discovery_only | rejected
    license: string | null
    redistribution_allowed: true | false | unknown
    snapshot_checksum: string | null
    verification_notes: string
    verified_by_agent_at: datetime
    human_source_decision: pending | approved | rejected

The source ID is stable even if a URL changes. A new edition or materially changed web page receives a new source ID.


## 10. Candidate Pair Schema

Each candidate_pairs.jsonl record should contain:

    schema_version: string
    pair_id: string
    record_version: integer
    status: discovered | source_verified | extracted | lean_drafted |
            automated_checked | review_pending | changes_requested |
            curation_approved | rejected | frozen
    domain: string
    difficulty: string
    contamination_risk: low | medium | high | unknown
    informal_theorem:
      original_statements:
        - source_id: string
          text_or_paraphrase: string
          verbatim: boolean
      normalized_statement: string
      variables: list
      assumptions: list
      conclusion: string
      equivalence_notes: string
    proof_variants:
      - variant_id: A | B
        source_ids: list[string]
        source_locators: list
        strategy_family: string
        strategy_realization: string
        proof_summary: string
        steps:
          - step_id: string
            text: string
            depends_on: list[string]
            source_support: list
            inference_flag: explicit | minor_bridge | substantial_gap
        required_signatures: list[string]
        incompatible_signatures: list[string]
        copyright_mode: paraphrase | licensed_extract | short_quote
    pair_analysis:
      same_theorem_evidence: string
      strategy_distinctness_evidence: string
      known_ambiguities: list[string]
    lean:
      declaration_name: string
      statement_type: string
      imports: list[string]
      lean_version: string
      mathlib_commit: string
      check_wrapper_path: string
      parse_status: pass | fail | not_run
      elaboration_status: pass | fail | not_run
      diagnostics_path: string | null
      statement_hash: string
      informal_equivalence_notes: string
    automated_checks:
      schema_valid: boolean
      both_sources_verified: boolean
      same_theorem_precheck: pass | fail | uncertain
      distinct_strategy_precheck: pass | fail | uncertain
      duplicate_precheck: pass | fail | uncertain
    review_ids: list[string]
    parent_record_hash: string | null
    record_hash: string
    created_at: datetime
    updated_at: datetime

The public record contains paraphrases and attribution by default. If source text is restricted, text_or_paraphrase must be a paraphrase and the exact private snapshot is referenced only by checksum.


## 11. Human Review Schema

Each human_reviews.jsonl record should contain:

    schema_version: string
    review_id: string
    pair_id: string
    record_version: integer
    record_hash: string
    reviewer_id: string
    reviewer_role: mathematical | lean_math | project_lead
    source_quality: approve | changes_requested | reject | not_applicable
    mathematical_correctness: approve | changes_requested | reject | not_applicable
    same_theorem: approve | changes_requested | reject | not_applicable
    strategy_distinctness: approve | changes_requested | reject | not_applicable
    lean_statement_equivalence: approve | changes_requested | reject | not_applicable
    copyright_handling: approve | changes_requested | reject | not_applicable
    overall_decision: approve | changes_requested | reject
    comments: string
    reviewed_at: datetime

A review applies only to the exact record hash. Any change to theorem text, proof summaries, sources, strategy labels, or Lean statement invalidates the affected approvals and creates a new record version.


## 12. Lean Statement Checking Without a Lean Proof

The agent stores only the theorem type needed by the prover. To test it without creating a proof, generate a temporary Lean file that defines the proposition as data:

    import Mathlib

    def CandidateStatement : Prop :=
      <the proposed theorem proposition>

    #check CandidateStatement

Run the file under the pinned project:

    lake env lean outputs/curation/lean_statement_checks/<pair_id>.lean

Passing this check proves only that Lean can parse and elaborate the proposition. It does not prove that the proposition is true or that it faithfully represents the informal theorem. Those are separate human review questions.

The automated checker must also:

- [ ] reject missing or floating toolchain metadata;
- [ ] reject imports outside the approved list unless justified;
- [ ] reject sorry, admit, axiom declarations, and embedded proof bodies;
- [ ] store stdout, stderr, exit code, and statement hash;
- [ ] check that every candidate has a unique declaration name;
- [ ] normalize formatting without changing semantics;
- [ ] keep the exact pre-normalization statement for audit;
- [ ] run simple type-boundary examples when feasible;
- [ ] never weaken a theorem merely to make elaboration pass.


## 13. Human Review Questions for Every Pair

### Source review

- [ ] Can the reviewer identify the author or editorial body?
- [ ] Is the source appropriate for mathematical evidence?
- [ ] Does the cited page or section actually contain the claimed theorem and strategy?
- [ ] Is the source stable enough for collaborators to inspect?
- [ ] Is the license or redistribution status recorded correctly?
- [ ] Has the agent avoided copying restricted text unnecessarily?

### Mathematical review

- [ ] Are all variables and assumptions explicit?
- [ ] Is proof A correct?
- [ ] Is proof B correct?
- [ ] Do A and B prove exactly the same conclusion?
- [ ] Are hidden side conditions the same?
- [ ] Are A and B mathematically different strategies?
- [ ] Could a model follow either strategy without inventing a missing central argument?
- [ ] Are the structured steps faithful to the source?

### Lean-statement review

- [ ] Do Lean variable types match the mathematical domains?
- [ ] Are all quantifiers preserved?
- [ ] Are all hypotheses preserved?
- [ ] Is the conclusion neither weaker nor stronger by accident?
- [ ] Are coercions and overloaded operations interpreted correctly?
- [ ] Are zero, empty-set, sign, finiteness, and denominator edge cases handled?
- [ ] Do Mathlib definitions match the intended mathematical objects?
- [ ] Does the declaration expose the same theorem to every proof condition?


## 14. Rejection Reasons

Use stable machine-readable rejection codes:

    SOURCE_NOT_HUMAN_VERIFIABLE
    SOURCE_TOO_WEAK
    SOURCE_UNAVAILABLE
    COPYRIGHT_UNCLEAR
    PROOF_A_NOT_SUPPORTED
    PROOF_B_NOT_SUPPORTED
    PROOF_INCOMPLETE
    MATHEMATICAL_ERROR
    THEOREMS_NOT_EQUIVALENT
    ASSUMPTIONS_DIFFER
    STRATEGIES_NOT_DISTINCT
    STRATEGY_DIFFERENCE_ONLY_STYLISTIC
    LEAN_STATEMENT_MISMATCH
    LEAN_STATEMENT_DOES_NOT_ELABORATE
    DOMAIN_OUT_OF_SCOPE
    DUPLICATE_THEOREM
    CONTAMINATION_TOO_HIGH
    REVIEWER_UNRESOLVED
    OTHER_WITH_EXPLANATION

Rejected records are retained. Never delete them from the curation history, silently repair them into new examples, or replace them without preserving the relationship between versions.


## 15. Batch Workboard

### Calibration

- [ ] Select two candidates from different domains.
- [ ] Complete the full agent workflow.
- [ ] Complete both human reviews.
- [ ] Revise schema and rubric.
- [ ] Freeze curation schema version 1.

### Batch 1 — approved pairs 1–5

- [ ] Agent discovery and source verification complete.
- [ ] Agent extraction complete.
- [ ] Lean statements elaborate.
- [ ] Mathematical review complete.
- [ ] Lean/math review complete.
- [ ] Revisions closed.
- [ ] Five pairs promoted.

### Batch 2 — approved pairs 6–10

- [ ] Agent discovery and source verification complete.
- [ ] Agent extraction complete.
- [ ] Lean statements elaborate.
- [ ] Mathematical review complete.
- [ ] Lean/math review complete.
- [ ] Revisions closed.
- [ ] Five pairs promoted.

### Batch 3 — approved pairs 11–15

- [ ] Agent discovery and source verification complete.
- [ ] Agent extraction complete.
- [ ] Lean statements elaborate.
- [ ] Mathematical review complete.
- [ ] Lean/math review complete.
- [ ] Revisions closed.
- [ ] Five pairs promoted.

### Batch 4 — approved pairs 16–20

- [ ] Agent discovery and source verification complete.
- [ ] Agent extraction complete.
- [ ] Lean statements elaborate.
- [ ] Mathematical review complete.
- [ ] Lean/math review complete.
- [ ] Revisions closed.
- [ ] Five pairs promoted.

### Batch 5 — approved pairs 21–25

- [ ] Agent discovery and source verification complete.
- [ ] Agent extraction complete.
- [ ] Lean statements elaborate.
- [ ] Mathematical review complete.
- [ ] Lean/math review complete.
- [ ] Revisions closed.
- [ ] Five pairs promoted.

### Batch 6 — approved pairs 26–30

- [ ] Agent discovery and source verification complete.
- [ ] Agent extraction complete.
- [ ] Lean statements elaborate.
- [ ] Mathematical review complete.
- [ ] Lean/math review complete.
- [ ] Revisions closed.
- [ ] Five pairs promoted.

### Final freeze

- [ ] Exactly 30 pairs approved.
- [ ] Domain and strategy distribution reviewed.
- [ ] Duplicate and contamination checks complete.
- [ ] All source links and locators rechecked.
- [ ] All record and statement hashes verified.
- [ ] Complete dataset loads through the benchmark schema.
- [ ] Private source materials excluded from the public export.
- [ ] Project lead signs the frozen manifest.


## 16. Agent–Human Handoff Rules

| Step | Agent owns | Human owns | Blocking output |
|---|---|---|---|
| Discovery | Search log and candidate pool | Domain redirection | Source-backed candidate |
| Source verification | Metadata, locator, license evidence | Reliability approval | Approved source record |
| Extraction | Normalized theorem, proof summaries, steps | Mathematical fidelity | Approved A/B extraction |
| Strategy analysis | Proposed labels and signatures | Distinctness decision | Approved strategy pair |
| Lean translation | Statement, imports, elaboration logs | Semantic equivalence | Approved Lean statement |
| Revision | Versioned response to comments | Reapproval | Matching record/review hashes |
| Promotion | Automated validation and export | Freeze authority | curation_approved record |

The agent should continue sourcing the next batch while up to ten records await review. It must not continue polishing a rejected pair unless a reviewer explicitly requests a revision.


## 17. Connection to the Existing Plans

### Connection to the ExecPlan

- [ ] Add the three curation schemas to the implementation schema milestone.
- [ ] Add source-registry and review-packet commands to the CLI.
- [ ] Add Lean proposition-only checking to the Lean checker.
- [ ] Make the benchmark importer accept only curation_approved records.
- [ ] Preserve record hashes in generation requests.
- [ ] Treat source and review data as immutable run inputs.
- [ ] Keep full proof formalization outside this curation critical path.

### Connection to the Human Plan

- [ ] Use Human Gate H2 for pair-level trust, adapted so Lean proofs are not required at curation stage.
- [ ] Assign the mathematical and Lean/math reviewers.
- [ ] Add weekly review slots for five-pair batches.
- [ ] Track source quality, math, strategy, and Lean equivalence separately.
- [ ] Keep unresolved pairs outside the approved count.
- [ ] Record the decision that synchronizes the older Lean-reference-proof requirement.

### Connection to the prover-facing dataset

- [ ] Export the exact Lean theorem statement and imports.
- [ ] Export proof A and proof B summaries and structured steps.
- [ ] Export strategy signatures needed for evaluation.
- [ ] Export source IDs and provenance without restricted source text.
- [ ] Export statement and record hashes.
- [ ] Do not export reviewer identities unless the release policy allows it.


## 18. Quality Metrics for the Curation Process

Track process quality without turning it into a substitute for human judgment:

- [ ] candidate-to-approval rate;
- [ ] rejection rate by reason;
- [ ] median agent revisions per approved pair;
- [ ] median human review time per pair;
- [ ] source-type distribution;
- [ ] proportion of pairs with A and B from independent sources;
- [ ] domain and strategy-family distribution;
- [ ] Lean-statement first-pass elaboration rate;
- [ ] informal-to-Lean changes requested by reviewers;
- [ ] unresolved-review count;
- [ ] duplicate-theorem count;
- [ ] proportion of records with redistribution restrictions;
- [ ] percentage of final text that is paraphrased versus licensed extraction.

Do not select examples because they make a particular model look good. Curation decisions occur before model outputs are inspected.


## 19. Open Decisions

- [ ] Decide whether one person may fill both human reviewer roles for low-risk pairs.
- [ ] Decide whether two independent mathematical approvals are required for all 30 pairs or only the pilot and a random audit.
- [ ] Decide the exact source-reliability threshold for mathematician-authored personal sites.
- [ ] Decide whether public-domain textbook proofs may be stored verbatim or should still be paraphrased.
- [ ] Decide the exact five-domain balance after the first 15 approved pairs.
- [ ] Decide whether any high-contamination classic theorem is kept as a familiar-control subset.
- [ ] Decide whether the original reference-Lean-proof gate is removed, made optional, or applied only to a smaller validation subset.
- [ ] Decide whether proof paraphrases are created during curation or after the 30 pairs are frozen.


## 20. Decision Log

- [x] 2026-07-23 — Target 30 human-approved A/B proof-strategy pairs.
- [x] 2026-07-23 — Let the agent discover a larger 45–60 candidate pool because human review will reject some pairs.
- [x] 2026-07-23 — Require both strategies to have traceable human-authored mathematical sources.
- [x] 2026-07-23 — Permit proof A and B to come from the same or different reliable sources.
- [x] 2026-07-23 — Store structured, source-faithful paraphrases by default instead of copying full copyrighted proofs.
- [x] 2026-07-23 — Require the agent to translate and automatically check the Lean theorem statement.
- [x] 2026-07-23 — Do not require a Lean proof during the 30-pair curation stage.
- [x] 2026-07-23 — Keep human approval authoritative for source trust, mathematics, strategy distinctness, and Lean equivalence.
- [x] 2026-07-23 — Preserve rejected candidates and all revised versions.
- [ ] YYYY-MM-DD — Record the synchronized final policy for reference Lean proofs.
- [ ] YYYY-MM-DD — Record the approved schema and rubric versions.
- [ ] YYYY-MM-DD — Record the final 30-pair manifest hash.


## 21. Immediate Next Actions

- [ ] Coding agent creates the JSON Schemas and empty JSONL files.
- [ ] Project lead assigns mathematical and Lean/math reviewers.
- [ ] Humans approve the source-quality rubric.
- [ ] Agent proposes two calibration pairs with complete source records.
- [ ] Humans complete calibration reviews.
- [ ] Schema and rubric version 1 are frozen.
- [ ] Agent begins the first five-pair batch and maintains the discovery/rejection logs.
