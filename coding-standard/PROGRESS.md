# Progress Log

Running log, newest entry first. Copy an entry template from
[PROGRESS_LOG.template.md](PROGRESS_LOG.template.md), fill it in, and prepend it here.

Two purposes: keeps the agent oriented across sessions (what's been built, what broke and
why, in what order), and serves as raw material for later retrospective analysis — an
agent can be run over this file to audit how the agentic workflow itself is going, not
just the code.

---

### 2026-07-24 — Add fourth proof-strategy discovery batch

- **Tier:** exploratory
- **File(s):** `data/benchmark/candidates/009-gcd-times-lcm.md`,
  `data/benchmark/candidates/010-bernoulli-nonnegative.md`,
  `data/benchmark/candidates/011-cauchy-schwarz-two-variable.md`
- **What:** Added three draft A/B theorem candidates with complete paraphrased proofs,
  precise source locators, strategy signatures, contamination assessments, and
  unverified Lean statement sketches.
- **Why:** Continued the reusable discovery workflow with two to three additional
  candidates outside the existing exclusion list.
- **How it works:** Full source documents were inspected for both claimed routes. The
  batch covers prime valuations versus coprime reduction, induction versus binomial
  expansion, and a direct Lagrange identity versus a discriminant argument.
- **Reused pattern or new one?** Reuses the numbered draft-candidate and human-review
  boundary. The two classic inequality candidates are explicitly marked high
  contamination risk rather than screened out silently.

### 2026-07-24 — Add third proof-strategy discovery batch

- **Tier:** exploratory
- **File(s):**
  `data/benchmark/candidates/007-odd-number-of-divisors-iff-square.md`,
  `data/benchmark/candidates/008-hockey-stick-identity.md`
- **What:** Added two draft A/B theorem candidates with complete paraphrased proofs,
  source locators, strategy signatures, contamination assessments, and unverified Lean
  statement sketches.
- **Why:** The reusable discovery prompt requests small batches of source-verified
  candidates whose two proofs have visibly different formal shapes.
- **How it works:** Each claimed route was checked in the full university-hosted source;
  the batch kept only the divisor-involution versus prime-exponent contrast and the
  induction versus largest-element double-counting contrast.
- **Reused pattern or new one?** Reuses the existing numbered draft-candidate format and
  review boundary; neither file is human-approved.

<!-- Newest entries go here, above this line. -->
