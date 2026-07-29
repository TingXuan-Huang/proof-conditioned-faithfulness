# Real-Backend Compatibility Report

**Status:** calibration checkpoint complete; awaiting human model-slate review  
**Date:** 2026-07-29  
**Scope:** one calibration theorem, condition `proof_a`, sample index `0`

This report covers compatibility testing only. It does not authorize a pilot, core run,
GPT-5.6 Terra request, use of Meta outputs as scientific data, or closure of any human
gate. All runs are under `outputs/calibration/`.

## Readiness

| Backend | Exact identity | Hardware and serving | Load/connect and generation | Artifacts, resume, and downstream | Measured result | Estimate for 45 / 270 requests | Limitation | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GPT-OSS | `openai/gpt-oss-120b` @ `b5c939de8f754692c1647ca79fbf85e8c1e70f8a` | 1x H200; native MXFP4; vLLM 0.19.1; Harmony / `openai_gptoss` parser | Passed; load 1,639 s; nonempty response | Checksummed raw/response passed; resume skipped 1/1; warmed child passed Lean, dependency probe, and evaluation preparation | 17.522 s; 181 output tokens; 10.330 tok/s; peak 142,251 MiB; $0 API cost | 40.46 min / 1.77 h serial generation | Nearly fills one H200; estimates exclude queue/checking | **ready** |
| Qwen | `Qwen/Qwen3-32B` @ `9216db5781bf21249d130ec9da846c4624c16137` | Required run: 1x H200 BF16; vLLM 0.19.1; official template; `qwen3` parser | Passed; load 687 s; nonempty response | Checksummed raw/response passed; resume skipped 1/1; checker classified `type_invalid` (`Nat.add_zero` omitted `n`); dependency/evaluation correctly skipped. Independent A100 response passed all downstream stages. | 18.650 s; 623 output tokens; 33.404 tok/s; corrected peak 130,983 MiB; $0 API cost | 25.44 min / 1.59 h serial generation | H200 sample was an invalid proof, which is allowed for compatibility; vLLM reserved most H200 memory | **ready**; A100 is a measured fallback |
| DeepSeek Prover | `deepseek-ai/DeepSeek-Prover-V2-7B` @ `a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b` | 1x L40 BF16; vLLM 0.19.1; pinned corrected tokenizer overlay; documented calibration prompt | Passed; load 466 s; nonempty, normally decoded response | Checksummed raw/response passed; resume skipped 1/1; checker classified `multiple_blocks`; dependency/evaluation correctly skipped | 13.879 s; 619 output tokens; 44.600 tok/s; corrected peak 41,781 MiB; $0 API cost | 18.18 min / 1.17 h serial generation | Model emits multi-declaration output under this recipe; single-proof extractor does not repair it | **fallback** pending prompt/output-contract decision |
| Meta Muse Spark 1.1 | API ID `muse-spark-1.1`; project revision label `meta-model-api-2026-07-28` | Meta OpenAI-compatible endpoint; approved external request; no local GPU | Passed; provider request ID persisted; nonempty response | Raw payload, usage, timing, cost, checksums passed; resume skipped 1/1; checker classified `syntax_invalid` because response included an extra `:=`; dependency/evaluation correctly skipped | 19.379 s; 111 input / 1,869 output tokens; 96.446 output tok/s; harness-settled $0.008082 | N/A: testing-only backend, excluded from pilot/core | Configured endpoint/ID worked live; current price still needs dashboard confirmation | **optional**, testing only |
| ProofBridge | upstream `465d2a03a2cfe839022d6c71b587544aae402d07` | Pinned public checkout | Probe ran and exited 78 before generation | Checksummed failure and raw diagnostic persisted; downstream unavailable | No generation metrics; $0 | N/A | Public release has no documented runnable inference entrypoint or trained checkpoint | **infeasible** from public release |
| ProofFlow | upstream `97f1b7be82380733fb0380973c164e40645ae9da`; Qwen revision above | 1x A100 80 GB; ProofFlow 1.0.0; local Qwen/vLLM 0.19.1 | Qwen loaded and returned HTTP 200; ProofFlow received `Nat.add_zero n`, then upstream `build_proof_graph` raised `RuntimeError` | Checksummed failure/raw diagnostic persisted; no terminal `GenerationResponse`, so resume/downstream could not run | Job 26.97 min; observed server generation about 14.3 tok/s; peak 73,927 MiB; $0 | N/A | Minimal fixture is incompatible with upstream proof-graph construction | **infeasible** for the current slate; best-effort attempt retained |

The time estimates use `load time + request count x measured single-request latency`.
They are optimistic calibration-prompt estimates and exclude queue time, Lean checking,
dependency probing, evaluation export, retries, and longer experimental outputs. Local
API cost is zero; cluster allocation cost is unknown and is not represented as zero.

## End-To-End Result

- Generation, verbatim response persistence, checksum verification, resume without a
  duplicate request, trusted Lean classification, conditional dependency probing, and
  evaluation preparation all executed successfully through the shared harness.
- A proof need not compile for backend compatibility. Invalid model outputs were retained
  verbatim and classified; dependency/evaluation stages were skipped only when the
  trusted Lean prerequisite failed.
- GPT-OSS and an independent Qwen A100 sample reached green Lean, dependency, and
  evaluation stages. Qwen H200, DeepSeek, and Meta reached those stages and recorded
  honest model-output failures.
- The Meta request was bound to the machine-readable approval and a $5.50 ceiling. The
  one request settled at $0.008082, and its immediate resume issued no second request.
  Meta output remains calibration-only.

## Verification

Final offline job `37869456` used verified snapshot commit `5ae84e759...` plus the
checksummed source overlay for `b7eb71fa...`:

```text
Mathlib warm-up: passed in 424.831 s
python -m pytest -q -p no:cacheprovider: 283 passed in 51.69 s
ruff check --no-cache src tests: passed
python -m pyright: 0 errors, 0 warnings, 0 informations
lake build: passed (one existing unused-variable warning)
```

Afterward, launcher-only commit `15fe536` corrected GPU peak parsing from string to
numeric comparison. `bash -n` passed, and a two-row regression fixture returned
`130983`, not `791`. Seven focused approval, missing-secret, ambiguous-retry,
kill/resume, and refusal tests passed in 0.44 s. An audit verified all 114 checksum
sidecars across the eight authoritative runs, with zero failures. Exact-secret-prefix
scans found zero tracked or calibration-artifact matches.

The initial direct `uv run pytest` did not test code: the sandbox could not write the
configured scrubbed uv cache. A direct `.venv` rerun then reached Lean and stalled on
shared GPFS metadata; it was stopped and replaced by the established node-local job.

## Evidence And Incidents

Authoritative run IDs:

- GPT-OSS: `calibration-gpt-oss-120b-37856915` and immutable warmed reassessment
  `calibration-gpt-oss-120b-reassess-warm-37868405`.
- Qwen H200: `calibration-qwen3-32b-37868476`; A100 downstream control
  `calibration-qwen3-32b-reassess-37868405`.
- DeepSeek corrected tokenizer: `calibration-deepseek-prover-v2-7b-37868477`.
- Meta: `calibration-meta-muse-spark-approved-20260729`.
- ProofBridge: `calibration-proofbridge-20260728`.
- ProofFlow: `calibration-proofflow-qwen3-32b-37868402`.

Operational issues fixed during bring-up were: pre-created SquashFS extraction targets,
missing generic Python under `--cleanenv`, cold Mathlib access, missing `libatomic` for
Pyright, missing-secret preflight ordering, DeepSeek tokenizer dispatch, and numeric GPU
peak accounting. Failed attempts remain distinguishable from model-output failures.

## Human Stop Gate

Stop here. Human review must select the final slate and decide whether DeepSeek's
multi-block output merits a prompt/contract change and whether either pipeline should be
replaced. Pilot/reference approval, Gate P/S/C/A, statistical decisions, and candidate
Status fields remain open. Revoke the Meta key that was pasted into chat and remove it
from the current shell with `unset META_MODEL_API_KEY`; create a fresh key only for a
future explicitly approved request.
