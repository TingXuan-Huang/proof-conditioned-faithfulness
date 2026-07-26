# T016 Reference Proof Screening Report

**Checkpoint:** 2026-07-26

**Project commit:** `a65e9d8fb34a689e8e3b9af5859497e4b0f43d4a`

**Human status:** Unreviewed. This report does not approve Gate P, Gate S, a candidate
Status, an import, or proof faithfulness.

## Scope

The ten submitted Route A/B drafts for proposed candidates 001, 033, 036, 040, and 041
were compile-screened without repairing proof text. A failing proof is a data outcome:
S3 is skipped, and the diagnostics are preserved. Only a proof accepted by the complete
trusted S2 predicate can proceed to S3.

The draft source is present in each candidate's committed reference brief under
`data/benchmark/reference-briefs/`. Exact files used by the batch are retained in the
gitignored artifact tree under `outputs/reference-proof-checks/37700033/sources/`.

## Per-route Results

Diagnostic compile job `37700033` used a separate Mathlib warm-up and a 600-second
per-route ceiling. It completed all ten routes without a timeout. For this table,
`prohibited_sorry` takes precedence; other elaboration/type diagnostics are summarized
as `type_invalid`. These nine failures predate the persisted one-body trusted runner and
are not claimed as full trusted-S2 artifacts.

| Route | Compiles | Screening category | S3 | Axiom/trust observation |
| --- | --- | --- | --- | --- |
| 001-A | no | `type_invalid` | skipped | failed elaboration; error recovery mentions `sorryAx` |
| 001-B | no | `type_invalid` | skipped | failed elaboration; error recovery mentions `sorryAx` |
| 033-A | no | `prohibited_sorry` plus type error | skipped | literal `sorry` at source line 18 |
| 033-B | no | `type_invalid` | skipped | failed elaboration; error recovery mentions `sorryAx` |
| 036-A | yes | `success` | success | trusted axioms: `Quot.sound`, `propext` |
| 036-B | no | `type_invalid` | skipped | missing `DecidablePred P`; error recovery mentions `sorryAx` |
| 040-A | no | `type_invalid` | skipped | Rat API/cast and parity elaboration errors |
| 040-B | no | `type_invalid` | skipped | Rat API/cast and coprimality elaboration errors |
| 041-A | no | `prohibited_sorry` plus type errors | skipped | two literal `sorry` occurrences, lines 35 and 40 |
| 041-B | no | `prohibited_sorry` plus type errors | skipped | literal `sorry` at line 46 |

The full unabridged diagnostics are in
`outputs/reference-proof-checks/37700033/results.json`. A compiler's `sorryAx` after a
failed elaboration is not counted as a literal source violation; literal token screening
is reported separately.

## Trusted 036-A Check

After node-local staging was corrected, SLURM job `37724510` completed in 1:39 with
exit `0:0` and no network access:

- fixed-source warm-up: success, 62.361 seconds;
- exact statement hash: matched;
- extraction, parser, and elaboration: success;
- candidate wall time: 4.781 seconds;
- prohibited-token findings: none;
- axiom set: `Quot.sound`, `propext`, both allowed;
- S3 dependency probe: success.

The deterministic request ID is
`299ebaf5d310700caa3af8ca89e2202ba919277f46616954acb5982023f43ed4`.
All ten persisted artifact sidecars were independently rehashed successfully. The
top-level summary SHA-256 is
`4a8564435f2a6e49500e647ae31516f6047e5c8d84e264a7de2dcf1e4cf584ee`.

S3 reports:

- provisional classification: `automation_bypass`;
- tactic evidence: `induction`, `explicit_local`, `automation`;
- explicit local names: `hcases`, `hn11`, `hsmall`;
- retained local-fact use: `hcases=true`, `hn11=false`, `hsmall=true`.

The Route-A brief explicitly permits `omega` for arithmetic side goals. Therefore the
machine classification is evidence for human review, not a rejection or a faithfulness
decision.

## Mechanical Brief Scan

The scan compared proof text with each route's "Must NOT appear" and both-route banned
lists, while respecting contextual exceptions stated in the brief.

| Route | Contextual banned-list hit |
| --- | --- |
| 001-A/B | none; `001-A` uses `norm_num` for a small coprimality fact, not the main goal |
| 033-A/B | none; Route A's `List.Perm.sum_eq` is explicitly required/exempt |
| 036-A/B | none; `omega` use in A follows witness construction/side arithmetic |
| 040-A/B | none; `decide` proves finite base facts, not the irrationality main goal |
| 041-A | none; `interval_cases` and concrete `norm_num` are Route-A requirements |
| 041-B | `decide` at source line 66; this brief bans `decide` in both routes |

The common no-escape-hatch scan separately finds `sorry` in three routes and four
literal locations: `033-A:18`, `041-A:35`, `041-A:40`, and `041-B:46`.

## Operational Failures

Jobs `37722631` and `37722668` failed before candidate execution because their one-off
script set `ELAN_HOME` to a launcher-only scrubbed directory. The error was a missing
`lake` binary inside that incorrectly selected toolchain. Leaving `ELAN_HOME` unset
matched the already-green gauntlet environment and produced successful job `37724510`.
Neither failed job says anything about the mathematical proof.

## Remaining Human Work

Humans must inspect the `036-A` S3 evidence and decide whether its automation is only
permitted side-goal arithmetic, approve or reject the proof, decide whether to repair or
replace the nine failed routes, and make every Gate-S and candidate-Status change. This
report intentionally leaves T016 open until that disposition is recorded.
