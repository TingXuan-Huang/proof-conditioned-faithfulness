# Analysis Decisions — Deferred, With a Hard Freeze Deadline

Status: **open**. These decisions — (a)–(e) plus the dispute rule (g) — are
deliberately deferred until after the pilot run, when real outputs make them concrete.
**Hard rule: all of them must be frozen before anyone inspects core-run results.** Choosing a metric or coding rule after seeing which
choice flatters the numbers invalidates the primary claim (garden of forking paths).
The pilot is exploratory — using pilot outputs to inform these choices is legitimate.

Owner: Tingxuan. Tracked as todo.md item T006.

## (a) Primary estimand — what is the paper's headline number?

Given proof A three times, suppose: sample 1 compiles and matches A; sample 2 compiles
but uses a different strategy; sample 3 looks like A but doesn't compile.

- **Strict end-to-end** (provisional recommendation): success = compiles AND matches.
  Score 1/3. Conservative; doesn't credit broken output.
- **Conditional on validity**: among compiling samples, how many match? 1/2. Flatters
  models that rarely compile but match when they do — a model could score 100% while
  failing 90% of the time. Report it, but labeled descriptive.

## (b) Sample pairing — how do A-runs pair with B-runs in the responsiveness formula?

Matched-own-target results, 3 samples each: given A = [yes, yes, no]; given B =
[no, yes, yes].

- **Pair by index**: (A1,B1),(A2,B2),(A3,B3) → success requires both sides match →
  fail, success, fail = 1/3. But sample #1 of A has no real relationship to sample #1
  of B — the pairing is a bookkeeping accident, unless deterministic seeds are used.
- **Proportions first** (provisional recommendation): per-condition rates 2/3 and 2/3 →
  both-directions rate 2/3 × 2/3 = 4/9 ≈ 0.44. No invented pairing; matches the
  theorem-as-analysis-unit principle. Index pairing survives as a sensitivity check for
  seed-supporting providers.

Same data, different answers (0.33 vs 0.44) — this is why it must be frozen in advance.

## (c) Ambiguity coding — what happens to "can't tell" outputs?

Example: given proof A (algebra), the model proves the goal with one `omega` automation
call — no visible strategy at all. Annotators mark it unresolved.

- **Conservative (provisional recommendation)**: unresolved counts as failure in the
  headline number, and the paper also reports bounds ("42%, and between 42% and 53%
  depending on unresolved coding").
- Never drop unresolved cases from the denominator — ambiguity concentrates in exactly
  the interesting conditions, so dropping is silent cherry-picking.

## (d) Uncertainty — how are error bars computed?

~810 core outputs are NOT 810 independent data points: all 27 outputs for one theorem
share that theorem's difficulty. Naive bootstrap → falsely tight intervals
(pseudo-replication; reviewers hunt for this).

- **Provisional recommendation**: theorem-clustered bootstrap — resample the 30 theorems
  with replacement, each chosen theorem brings its whole 27-output bundle; 10,000
  replicates, fixed seed; 95% interval from the spread. Mixed-effects logistic model
  strictly secondary (30 clusters is too few to lean on it).

## (e) Annotator agreement — when do we trust the human labels?

Two annotators label independently. Raw agreement misleads when one label dominates
(two people guessing "matches A" 90% of the time agree often by chance). Gwet's AC1
corrects for chance and stays stable under label imbalance (unlike Cohen's kappa, which
is kept only as a sensitivity statistic).

- **Provisional threshold recommendation**: AC1 ≥ 0.7 → labels trustworthy; 0.5–0.7 →
  marginal, adjudicate every disagreement and disclose prominently; < 0.5 → rubric
  failure, rewrite guidelines and relabel.

## (g) Dispute rule — when does a core case get reference Lean proofs?

Core pairs freeze on statement + signatures only; reference Lean proofs are added
during core annotation "where strategy expressibility is disputed" (PLAN.md Decision
Log). Left informal, "disputed" becomes a post-hoc judgment call made after seeing
which outputs are inconvenient (Codex review, 2026-07-24). So the trigger must be
mechanical and frozen at T006 with (a)–(e).

Example: on theorem 014, annotator 1 codes a sample "matches B (Cassini certificate)",
annotator 2 codes it "unresolved — can't tell if the certificate route was genuinely
followed or the goal fell to automation." Does this pair now get agent-drafted,
human-approved reference proofs to calibrate what route B formally looks like?

- **Provisional recommendation**: a core pair becomes disputed when, after independent
  labeling and before adjudication, EITHER (i) the two annotators disagree on the
  strategy label for ≥2 samples of that pair, OR (ii) either annotator marks
  strategy-expressibility uncertainty (a dedicated checkbox, not free text) for that
  pair. Disputed pairs get reference proofs drafted/approved BEFORE adjudication of
  that pair, and the event is logged in the annotation record.
- Rejected alternative: "annotators may request references freely" — unbounded human
  cost and invites references exactly where results look bad, which is the leak this
  rule exists to plug.

## (f) Dependency — second annotator

Everything in (e) presupposes two qualified annotators. Not yet recruited. Options:
recruit one mathematically-qualified person for bounded hours (calibration = 5 theorems;
humans label disagreements + a 25% audit, not everything), or preregister a weaker
single-annotator + LLM-judge design and accept the reviewer discount. Needs an owner
and a date; blocks the annotation phase, not the freeze of (a)–(e).
