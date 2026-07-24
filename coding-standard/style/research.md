# Research/ML Style & Review

**This file is not a peer of `python.md`/`shell.md`/`markdown.md`.** Those are per-
language style rules. This is a **second, add-on review pass**, run by its own agent,
specifically for ML/research-flavored code — it runs *in addition to* the normal
[CODE_REVIEW.md](../CODE_REVIEW.md) pass, never instead of it. Invoke it when a change
involves models, tensors, or anything headed toward publication; skip it for code that
doesn't touch any of that (a plain data-wrangling script, a shell utility).

Same anatomy as the rest of the kit: **Rules** → **Checklist** → **Reflection
questions**, tagged `[always]`/`[floor]`/`[lib]` per [README.md](../README.md) §2, plus
a `[publish]` tag scoped to the publish gate specifically.

*Status: numerical/ML testing strategies (purity tests, invariant tests, deterministic
fixtures) deliberately left out of this draft — pending additional sources on testing
strategy to be folded in together later.*

## 1. Tensor shape-suffix naming

**Rules**
- Establish a single-letter dimension key once per codebase — e.g. `B`=batch,
  `L`=sequence length, `D`=model dimension, `V`=vocab size, `H`=attention heads,
  `K`=key/value size — and document it once (module docstring or a shared constants
  file), not reinvented per-file.
- Append the relevant letters as a suffix to every tensor variable name: `input_ids_BL`,
  `hidden_BLD`, `logits_BLV`. The suffix should make the tensor's rank and the meaning
  of each axis legible without tracing through the code.
- Works across frameworks (PyTorch, JAX, NumPy) — the convention is about the variable
  name, not any framework-specific typing mechanism.

**Checklist**
- `[lib]` Every tensor variable in a promoted function carries a shape suffix.
- `[always]` The dimension key is defined once and referenced, not redefined ad hoc.

**Reflection questions**
- If I read this tensor's name with no other context, do I know its rank and what each
  axis means?

**Example**
```python
"""Dimension key: B=batch, L=seq_len, D=model_dim, V=vocab_size, H=n_heads, K=head_dim."""

def attention(query_BLHK, key_BLHK, value_BLHK):
    scores_BLLH = torch.einsum('blhk,bmhk->blmh', query_BLHK, key_BLHK)
    weights_BLLH = torch.softmax(scores_BLLH / (query_BLHK.shape[-1] ** 0.5), dim=2)
    return torch.einsum('blmh,bmhk->blhk', weights_BLLH, value_BLHK)
```

Source: Noam Shazeer, "Shape Suffixes: Good Coding Style" (Character.AI, 2024).

## 2. Model/system architecture separation

**Rules**
- Keep the bare architecture (an `nn.Module` with just `__init__` and a pure
  `forward()`) separate from the "system" class/function that orchestrates training —
  optimizer, loss computation, logging, checkpointing.
- `forward()` answers "what does this model compute, given input" — nothing else. It
  should never depend on an optimizer, a loss weight, or a logger existing.
- Framework-agnostic — this isn't scoped to PyTorch Lightning specifically, though
  Lightning's `LightningModule`/`training_step()` split is one concrete implementation
  of the same principle.

**Checklist**
- `[lib]` Can the model class be imported and used for inference (e.g. loading a
  checkpoint for analysis) without importing any training-only code?
- `[lib]` Does `forward()` do anything beyond computing the model's output — logging,
  loss computation, optimizer steps?

**Reflection questions**
- If I needed this model's activations for an unrelated analysis six months from now,
  would I have to import training machinery I don't need to get them?

**Example** — a sparse autoencoder, separated:
```python
class SparseAutoencoder(nn.Module):
    """The model — architecture only, nothing about how it's trained."""
    def __init__(self, input_dim, hidden_dim):
        super().__init__()
        self.encoder = nn.Linear(input_dim, hidden_dim)
        self.decoder = nn.Linear(hidden_dim, input_dim)

    def forward(self, x):
        hidden = torch.relu(self.encoder(x))
        reconstruction = self.decoder(hidden)
        return reconstruction, hidden


class SAETrainingSystem:
    """The system — owns a SparseAutoencoder, adds training-specific logic."""
    def __init__(self, model: SparseAutoencoder, lr, sparsity_weight):
        self.model = model
        self.optimizer = torch.optim.Adam(model.parameters(), lr=lr)
        self.sparsity_weight = sparsity_weight

    def training_step(self, batch):
        reconstruction, hidden = self.model(batch)
        recon_loss = F.mse_loss(reconstruction, batch)
        sparsity_loss = hidden.abs().mean()
        loss = recon_loss + self.sparsity_weight * sparsity_loss
        loss.backward()
        self.optimizer.step()
        wandb.log({"loss": loss.item()})
        return loss
```

Later, using the trained model for interpretability work — no optimizer, no sparsity
weight, no logging, just the model doing what a model does:
```python
model = SparseAutoencoder(input_dim=768, hidden_dim=4096)
model.load_state_dict(torch.load("checkpoint.pt"))
model.eval()
_, hidden_activations = model(some_inputs)
```

Source: PyTorch Lightning style guide (Systems vs. Models), generalized beyond Lightning
specifically.

## 3. Decouple data loading from the model

**Rules**
- Data loading/preprocessing lives in its own class or module, separate from the model —
  a "DataModule" pattern, whether or not you're using Lightning's actual `DataModule`
  class. This makes datasets hot-swappable against the same model (benchmark the same
  architecture on a new dataset without touching model code) and makes splits/transforms
  documented and shareable rather than implicit in whatever script happened to load the
  data.
- A data-loading module should be able to answer, on its own, without reading model
  code: what splits exist, how many samples per split, what transforms were applied.

**Checklist**
- `[lib]` Could this model be pointed at a different dataset by swapping only the data
  module, with zero changes to model code?
- `[lib]` Can I find split sizes and transforms without reading the training script?

**Example**
```python
class MyDataModule:
    """Decouples data loading from the model — what splits, how many samples, what
    transforms."""
    def __init__(self, data_dir, batch_size=32):
        self.data_dir = data_dir
        self.batch_size = batch_size

    def setup(self):
        self.train_dataset = load_split(self.data_dir, "train", transform=TRAIN_TRANSFORM)
        self.val_dataset = load_split(self.data_dir, "val", transform=EVAL_TRANSFORM)
        self.test_dataset = load_split(self.data_dir, "test", transform=EVAL_TRANSFORM)

    def train_dataloader(self):
        return DataLoader(self.train_dataset, batch_size=self.batch_size, shuffle=True)

    def val_dataloader(self):
        return DataLoader(self.val_dataset, batch_size=self.batch_size)
```

Source: PyTorch Lightning style guide (DataModules), generalized beyond Lightning.

## 4. Notebook hygiene

**Rules**
- Notebooks are for literate programming — narrative + code + graphics interleaved —
  not for pipelines, long-running training, or function/class definitions. Those live in
  `src/` modules and get imported into the notebook.
- **Restart kernel, run all cells, before committing.** A sourced stat worth taking
  seriously: **~75% of GitHub notebooks fail to run top-to-bottom** without errors —
  this is a real, common failure mode, not a hypothetical one.
- No fixed runtime cap. Compute-heavy cells (model training, real sweeps) legitimately
  take a long time, and that's fine — the underlying principle is "don't embed your full
  pipeline logic in a notebook," not "notebooks must be fast." If a notebook is slow
  because of unnecessary duplicate computation or leftover exploratory cruft, that's the
  actual signal to clean up — being slow because it's doing real work isn't a problem.
- Start each notebook with 3-5 bullet points of intended analysis outcomes, to prevent
  scope creep as the notebook grows.
- `%load_ext autoreload` / `%autoreload 2` for live module editing without kernel
  restarts while developing `src/` code alongside a notebook that uses it.
- `jupytext` for a markdown-based notebook representation — makes diffs and refactoring
  sane under version control, where raw `.ipynb` diffs are close to unreadable.

**Checklist**
- `[floor]` Notebook restarts and runs top-to-bottom cleanly before being committed.
- `[floor]` Pipeline/training logic lives in `src/`, not inline in notebook cells.

Source: Good Research Code Handbook, "Keep things tidy" (runtime-cap guidance adapted
for ML workloads per user judgment — the source's original 1-minute target doesn't fit
compute-heavy research code).

## 5. Publish gate

Fires when code is headed toward accompanying a paper or public release — in addition
to, not instead of, the normal promotion review ([CODE_REVIEW.md](../CODE_REVIEW.md)
§10).

**Rules**
- **Dependency spec**: `requirements.txt`/`environment.yml`/`setup.py` present, with
  install instructions written for someone with minimal background — not just a bare
  `pip install -r requirements.txt` with no context on Python version or GPU/CUDA
  requirements if relevant.
- **Training code**: the actual script(s) that produced the paper's headline numbers,
  with the real hyperparameters used — not hyperparameters described in prose that a
  reader has to reconstruct. Runnable on a different dataset, not hardcoded to the
  paper's exact data path.
- **Evaluation code**: the exact eval/metric-computation code ships too, not just a
  description — subtle procedural choices (edge-case handling, exact preprocessing) are
  exactly what silently produces irreproducible numbers if left undocumented.
- **Pre-trained models/checkpoints**: released where feasible, so results can be
  verified or built upon without forcing an expensive re-run.
- **README with a results table + exact reproduction commands**: someone should be able
  to go from a fresh clone to reproducing the paper's headline number by copy-pasting
  commands from the README, not by reverse-engineering the codebase.
- **Submit data to a DOI-issuing repository** (Figshare, Dryad, Zenodo) alongside the
  code — data is as much a research product as the paper itself, and a DOI is what
  makes it findable and citable independent of wherever the code repo happens to live.

**Checklist**
- `[publish]` Dependencies pinned and installable from a clean environment.
- `[publish]` Training script(s) present with the actual hyperparameters used for the
  paper's results, not just described.
- `[publish]` Evaluation code present and matches what actually produced the paper's
  numbers.
- `[publish]` Pre-trained checkpoints released, or an explicit note on why not.
- `[publish]` README results table + copy-pasteable reproduction commands verified to
  actually work from a clean clone.
- `[publish]` Data submitted to a DOI-issuing repository, or an explicit note on why not
  (e.g. licensing restrictions).

**Reflection questions**
- If I handed this repo to a stranger with no other context, could they reproduce the
  paper's Table 1 by only reading the README?
- Is there a hyperparameter or preprocessing choice that only lives in my head right
  now?

Source: Papers with Code, "Releasing Research Code" (NeurIPS 2021 official guidelines);
DOI-repository item from Wilson et al., "Good Enough Practices in Scientific Computing"
(PLOS Comp Bio, 2017), practice 1g.
