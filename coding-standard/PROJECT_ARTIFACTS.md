# Project Artifacts — Proof-Conditioned Lean Faithfulness Study

Two sections, two different authors — see [README.md §6](README.md#6-load-bearing-artifacts--the-project-artifact-index).
Fill in the project name above and the load-bearing artifacts below when this kit is
copied into a project. Leave both sections empty otherwise — this file starts blank.

## Load-bearing artifacts

*Human-written. The files listed here are ones I've personally read and can explain
without relying on an agent's summary.*

<!--
### path/to/file.py

What it is, why it's load-bearing for this project, and a short explanation in my own
words of what it does.
-->

## Everything else (agent-maintained)

*Agent-written. One short entry per file that isn't load-bearing — logged by the coding
agent as files are written, not read in full by the human.*

<!--
### path/to/other_file.py

One or two sentence summary of what this file does.
-->

### .gitignore

Excludes generated environments, run outputs, caches, and third-party pipeline clones.

### README.md

Provides project orientation, implementation status, and reproducible setup pointers.

### pyproject.toml

Defines the Python package, frozen dependency groups, CLI entry point, and tool settings.

### todo.md

Tracks stakes gates, human-owned inputs, deferred design work, and completed checks.

### docs/SERVER-HARNESS-RUNBOOK.md

Defines cluster execution, storage, secret, approval, model-serving, and recovery rules.

### docs/HUMAN-REVIEW-TODO.md

Collects the unchecked human reproduction, code-review, billing, research-decision, and
release gates with exact commands and links to observed evidence.

### docs/plans/active/PLAN.md

Controls stage exits, ordered experiment gates, decisions, and the active progress log.

### ProofFaithfulness.lean

Root Lean module used by `lake build` to verify the pinned scaffold.

### lakefile.toml

Lake package configuration pinned to the project's Mathlib dependency.

### lake-manifest.json

Resolved Lake dependency manifest for reproducible Lean builds.

### lean-toolchain

Pins the exact Lean toolchain used by the trusted checker.

### schemas/README.md

Documents the generated JSON Schema artifacts and their regeneration command.

### schemas/BenchmarkRecord.schema.json

Generated schema for benchmark theorem/proof-pair records.

### schemas/GenerationRequest.schema.json

Generated schema for fully identified generation requests.

### schemas/GenerationResponse.schema.json

Generated schema for successful normative response artifacts.

### schemas/LeanCheckResult.schema.json

Generated schema for normalized trusted-checker results.

### schemas/StrategyJudgment.schema.json

Generated schema for independent strategy judgments.

### schemas/StepAlignment.schema.json

Generated schema for informal-to-formal step alignments.

### schemas/CounterfactualEvaluation.schema.json

Generated schema for derived sample-level evaluations.

### src/proof_faithfulness/artifacts.py

Provides crash-recoverable, atomic, checksummed, freeze-aware run storage.

### src/proof_faithfulness/cli.py

Defines non-secret environment/model inspection and guarded schema export commands.

### src/proof_faithfulness/ids.py

Computes canonical response-affecting generation request identifiers.

### src/proof_faithfulness/schema.py

Defines immutable benchmark, generation, checker, and evaluation data contracts.

### src/proof_faithfulness/models/__init__.py

Exports the public model/prover adapter interfaces and configuration types.

### src/proof_faithfulness/models/base.py

Defines exact prompt hashing, capabilities, normalized results, and adapter protocol.

### src/proof_faithfulness/models/config.py

Validates the normative model-slate YAML and commit-bound pipeline runtime settings.

### src/proof_faithfulness/models/factory.py

Constructs concrete model adapters from validated configuration.

### src/proof_faithfulness/models/mock.py

Implements deterministic offline inference for harness smoke tests.

### src/proof_faithfulness/models/openai_compat.py

Implements bounded single-choice OpenAI-compatible transport and cost accounting.

### src/proof_faithfulness/models/pipeline.py

Wraps ProofBridge/ProofFlow-style tools with commit and process-lifecycle checks.

### tests/fixtures/fake_prover_pipeline.py

Executable JSON request/response fixture for subprocess adapter tests.

### tests/unit/test_artifacts.py

Exercises artifact atomicity, recovery, checksums, traversal, and freeze behavior.

### tests/unit/test_cli.py

Exercises CLI overwrite refusal and non-secret configuration inspection.

### tests/unit/test_ids.py

Exercises deterministic and response-sensitive request identity generation.

### tests/unit/test_model_adapters.py

Adversarially exercises model HTTP, paid refusal, and prover subprocess boundaries.

### tests/unit/test_result_schemas.py

Exercises cross-stage generation, checking, judgment, and evaluation contracts.

### tests/unit/test_schema.py

Exercises benchmark graph, freeze, axiom-policy, and generation request validation.

### tests/unit/test_schema_exports.py

Ensures committed JSON Schemas exactly match their Pydantic source models.

### data/benchmark/candidates/007-odd-number-of-divisors-iff-square.md

Draft candidate contrasting a complementary-divisor involution with a
prime-exponent divisor-count proof. Both routes are sourced to Arup Guha's UCF
number-theory lecture notes.

### data/benchmark/candidates/008-hockey-stick-identity.md

Draft candidate contrasting induction via Pascal's rule with a direct subset
count partitioned by largest element. The routes are sourced to UC Berkeley,
Ohio State, and UC Davis teaching materials.

### data/benchmark/candidates/009-gcd-times-lcm.md

Draft candidate contrasting prime-valuation arithmetic with reduction to a
coprime pair and the defining property of lcm. The routes are sourced to
Cornell and University of Maryland course materials.

### data/benchmark/candidates/010-bernoulli-nonnegative.md

Draft Bernoulli-inequality candidate contrasting induction on the exponent
with a nonnegative binomial remainder. The routes are sourced to UC Davis and
an Eric Weisstein reference page archived by Michigan State University.

### data/benchmark/candidates/011-cauchy-schwarz-two-variable.md

Draft two-variable Cauchy–Schwarz candidate contrasting the Lagrange identity
with an auxiliary quadratic and discriminant argument. The routes are sourced
to named lecture notes and MIT ESP course material.
