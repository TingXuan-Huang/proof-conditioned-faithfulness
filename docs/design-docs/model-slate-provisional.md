# Model Slate — Provisional (IDs freeze at PLAN.md 2.4 smoke test)

Status: PROVISIONAL. This doc answers "what actually runs where" so S4 adapter code
can be written before slate freeze. Exact model IDs/revisions/decoding configs are
frozen only at the 2.4 smoke test, into EXPERIMENT-SPEC.md §3. Decision owner for
the freeze: Tingxuan.

## The architectural fact that shapes S4

vLLM serves any HF model behind an **OpenAI-compatible HTTP endpoint**. Therefore
ONE OpenAI-style adapter (configurable base_url, api_key name, model id, prompt
template, decoding params) covers categories 1-3. Only category 4 (pipelines) needs
bespoke adapters. Write S4 as:

    adapters/openai_compat.py   # frontier API + local vLLM (general + provers)
    adapters/proofbridge.py     # wraps the ProofBridge repo's entrypoint
    adapters/proofflow.py       # wraps the ProofFlow repo's entrypoint

Model identity lives ONLY in configs/models/*.yaml (id, revision hash, base_url,
secret NAME, decoding recipe, concurrency cap) — never in code.

## Category by category

### 1. Frontier API (no GPU; the API budget lives here)
Runs in the provider's cloud; the server makes HTTPS calls. Needs: one API key
(secret NAME in config, value via env per RUNBOOK §3) and outbound network — if
compute nodes are offline (RUNBOOK §1 check), these jobs run from the login node.
Provisional pick: whichever provider a key exists for (GPT-5.x-class / Claude
Sonnet / DeepSeek API — the last is cheapest). One model suffices.

**Consumer subscriptions (ChatGPT Plus, Claude Pro/Max) can NEVER be slate models**
(decision 2026-07-24): chat apps inject hidden system prompts/tools/memory and
don't pin model revisions (breaks the Scientific Contract), automating them
violates ToS, and they can't produce auditable request logs. Subscriptions fund
the dev/review agents (Claude Code, Codex); the API funds the experiment.
The same applies to using Claude Code/Codex as generators — their harness
contaminates the sample.

**Cost lever — batch APIs**: providers' batch endpoints (e.g. Anthropic Message
Batches, OpenAI Batch API) run at ~50% of standard prices with ~1-24h turnaround
— a perfect fit for our non-interactive, precomputed request lists (`custom_id`
maps 1:1 onto our deterministic request IDs; results arrive unordered, keyed by
custom_id, which our resume logic already assumes). S4 SHOULD support a batch
transport for pilot/core full runs; keep the synchronous path for smoke slices.

### 2. Open-weight general (cluster GPU via vLLM)
`vllm serve <model>` inside a SLURM GPU job; harness talks to localhost. Pin the
exact HF revision hash. Provisional pick by GPU budget (T008 pending):
≥4×80GB → Qwen2.5-72B-Instruct; 2×80GB → Qwen2.5-32B-Instruct; 1 GPU →
Qwen2.5-14B-Instruct. Sizing numbers are approximate (bf16); quantized variants
are a fallback but must be recorded as a deviation.

### 3. Specialized Lean prover (cluster GPU via vLLM)
Same serving path; different prompt template + documented decoding recipe (recipes
override our temperature-0.2 default; deviations recorded — Decision Log
2026-07-24; identical low-temp samples are retained as data, never resampled).
Provisional anchor: **DeepSeek-Prover-V2-7B** (single GPU, Lean 4 + Mathlib
native, unproblematic vLLM serving). Add Goedel-Prover-V2-32B and/or a
Kimina-Prover distill if quota allows. ≥1 prover is required by the category rule.

### 4. Proof-conditioned pipelines (their own repos)
Clone ProofBridge / ProofFlow, run per their READMEs, wrap entrypoints in a
pipeline adapter. **ProofBridge is scientifically load-bearing** (Thread A
critiques its SC metric) — integrate it first; ProofFlow second. Riskiest
integrations: research code, Lean-version coupled (~4.15 — the reason for our
provisional toolchain pin). Per PLAN 2.4: record failed integrations with reasons
rather than silently omitting.

## Operational rules (RUNBOOK cross-refs)

- One model resident per GPU job: serve → run batch → shut down → next model
  (RUNBOOK §7). No co-residency without measured headroom.
- Every paid request needs an approvals/ record (§8); local vLLM inference is
  free (GPU time aside) and needs none.
- Smoke test per model at 2.4: 1 theorem × 1 condition × 1 sample end-to-end;
  record id/revision/quantization/context/GPU/cost; then freeze into
  EXPERIMENT-SPEC.md §3.

## S4 implementation contract (the coding agent writes code to THIS)

Everything below is normative for S4. If reality forces a deviation, record it in
PLAN.md's Decision Log — don't silently improvise.

### 1. Model config file — one YAML per slate model, this exact shape

    # configs/models/deepseek-prover-v2-7b.yaml
    key: deepseek_prover_v2_7b       # slate key; appears in request IDs and manifests
    category: prover                 # frontier_api | open_weight | prover | pipeline
    provider: vllm                   # vllm | openai_compat_api | proofbridge | proofflow
    model_id: deepseek-ai/DeepSeek-Prover-V2-7B
    revision: null                   # FULL HF commit hash — frozen at 2.4, null until then
    base_url: http://localhost:8000/v1   # API providers: the https endpoint
    api_key_env: null                # secret NAME for API providers (e.g. FRONTIER_API_KEY)
    chat_template: prover_deepseek_v1    # names a file in prompts/; hashed into request IDs
    decoding:                        # documented model recipe WINS over global defaults;
      temperature: 1.0               # a deviation from our defaults is recorded here + Decision Log
      top_p: 0.95
      max_tokens: 8192
      seed_base: 20260724            # per-request seed = seed_base + sample_index
    concurrency: 4                   # RUNBOOK §7 cap
    pricing_usd_per_mtok: {input: 0.0, output: 0.0}   # 0 for local inference
    pipeline_commit: null            # pipeline category only: pinned git commit of their repo

### 2. GenerationResponse artifact — responses/<request_id>/response.json

Required fields (S1 Pydantic model must match): `request_id`, `model_key`,
`revision`, `raw` (the provider's verbatim response payload — never discarded),
`text` (extracted completion), `finish_reason`, `usage` {input_tokens,
output_tokens}, `usd_cost` (usage × pricing config; 0.0 local), `latency_s`,
`started_at`, `completed_at`, `harness_git_commit`. Plus a sha256 sidecar per the
S1 artifact rules. The extractor that turns `raw` into `text` follows S2's rules
(may strip fences, may NOT repair).

### 3. Prompt template contract

`prompts/` holds versioned template files (`theorem_only_v1.txt`,
`preservation_v1.txt`, `validity_only_v1.txt`, `repair_v1.txt`, plus per-prover
chat templates). Template variables, double-brace style: `{{lean_statement}}`,
`{{imports}}`, `{{informal_proof}}` (absent in theorem_only). The mapping
condition → (system template, user template) lives in
`configs/experiment/conditions.yaml`, not in code. `prompt_hash` and
`chat_template_hash` in the request-ID formula are sha256 over the raw template
file bytes — so editing a template automatically changes every downstream
request ID (that is the point).

### 4. vLLM server lifecycle — job script owns it, not the harness

The SLURM job script: starts `vllm serve` in the background, polls
`GET /health` (timeout ~10 min — model load is slow), then runs
`proof-faithfulness run ...`, and kills the server via an EXIT trap (fires on
success, failure, and preemption alike). The harness only ever talks to
`base_url` and treats connection-refused as a retryable transport error.

### 5. Batch transport (openai_compat_api providers only)

Optional second transport for pilot/core full runs at ~50% cost: build the
provider's batch-input JSONL with `custom_id = request_id`, submit, poll,
fetch results, and write each result through the SAME GenerationResponse
artifact writer as the sync path (identical on-disk outcome; results arrive
unordered — key strictly by custom_id). Smoke slices always use the sync path.
If the batch job partially fails, the resume logic already handles it: missing
request_ids simply get re-sent.

### 6. Pipeline adapters (ProofBridge / ProofFlow)

Clone into `third_party/<name>/` (gitignored) at the commit pinned in
`pipeline_commit`; run per their own README/entrypoints; the adapter's ONLY
obligation is to emit the same GenerationResponse artifact as every other
provider. Integration failures are recorded per PLAN 2.4, never silently
dropped.

## Blockers for the freeze

1. T008 GPU facts (count/VRAM/partitions) — gates category 2/3 sizing.
2. Which frontier API key(s) the user provisions on the server (RUNBOOK §3).
3. ProofBridge/ProofFlow integration outcomes at 2.4.
