# Project Setup

**Research-project-specific.** This file covers one-time setup for a new research
project — if the work isn't a research project (e.g. general tooling, a non-research
codebase), skip this file entirely; don't copy it into non-research work.

Read once, at project creation. Everything else in `coding-standard/` (README.md,
CODING.md, CODE_REVIEW.md, style guides) is consulted on an ongoing basis; this file
isn't — it's a checklist you run through once and then forget about.

## 1. Default project unit

Default: **one project = one paper = one folder = one git repository.** This maps
cleanly to how research actually gets organized and cited. Exception: reusable tooling
used across multiple papers gets its own separate repository rather than living inside
any one paper's project folder.

## 2. Git init + GitHub sync

Initialize git and push to GitHub from day one — don't wait until the project feels
"real enough" to version control.

```bash
mkdir project-name && cd project-name
git init
echo "# project-name" >> README.md
git add README.md
git commit -m "First commit"
git branch -M main
git remote add origin https://github.com/<you>/project-name.git
git push -u origin main
```

**Commit cadence**: aim for a few times a day to a few times a week. One commit = one
coherent unit of related work (e.g. changes across 3 files that together add one piece
of functionality is one commit, not three).

## 3. Virtual environment

A project without a documented, isolated environment is not reproducible on another
machine or by future-you in six months. Conda is the default for data-science-heavy
Python work.

```bash
conda create --name project-name python=3.11
conda activate project-name
conda install pandas numpy scipy matplotlib  # conda packages first
pip install <anything-conda-doesn't-have>     # pip packages second
```

Installing pip packages *before* conda packages can destabilize conda's dependency
resolver — always conda first, pip second. Export the environment for reproducibility:

```bash
conda env export > environment.yml
```

## 4. Project skeleton

```
project-name/
|-- coding-standard/       # this kit — README, CODING, CODE_REVIEW, style/, PROJECT_ARTIFACTS.md, etc.
|-- data/                  # raw data + metadata — read-only after ingest
|-- docs/                  # manuscript drafts, lab notebook, changelog
|-- results/                # generated outputs — checkpoints, figures, tables
|-- scripts/                 # driver scripts, notebooks, anything directly executed
|-- src/                    # importable library code — see packaging below
|-- tests/
|-- .gitignore
|-- environment.yml
|-- README.md               # PROJECT-facing README — see disambiguation note below
|-- setup.py
```

Name files by what they contain, not by sequence number — `bird_count_table.csv`, never
`result1.csv`. Sequence numbers drift out of sync as a project evolves; content-based
names don't.

If data lives across multiple tables that get joined (e.g. subject demographics in one
table, trial-level measurements in another), use one consistent identifier format
everywhere — always `"14025"`, never `"14,025"` in one table and `"014025"` in another.
Inconsistent ID formatting is a common source of silent merge bugs.

## 5. Pip-installable package (not `sys.path` hacking)

Importing your own `src/` code from `scripts/` needs to actually work. The tempting
shortcut — appending `src/` to `sys.path` at the top of every script — is brittle: it
hardcodes folder paths in multiple places, breaks when folders move, breaks on other
machines, and defeats IDE autocomplete since the IDE can't see a dynamically-modified
path.

Instead, make the project an editable pip-installable package:

```python
# setup.py, at project root
from setuptools import find_packages, setup

setup(
    name='src',
    packages=find_packages(),
)
```

```bash
touch src/__init__.py
pip install -e .
```

The `-e` flag means edits to `src/` take effect immediately without reinstalling. After
this, `import src.whatever` works from any script, any directory, any IDE — no path
hacking required.

## 6. README disambiguation

There are **two different `README.md` files** in this tree — don't confuse them:

- **`<project-root>/README.md`** — project-facing. One-sentence description, extended
  explanation, install instructions, codebase orientation, links to the paper, license.
  This is what a stranger (or future-you) reads first.
- **`coding-standard/README.md`** — the standard's own shared invariants (tiers,
  promotion triggers, stakes gate, etc.). Not project-specific; this is the kit's
  internal documentation, not the project's.

## 7. Initialize the kit's tracking files

Copy `coding-standard/` into the project first, then:

- Fill out **`coding-standard/PROJECT_ARTIFACTS.md`** — declare this project's
  load-bearing artifact(s) (see `coding-standard/README.md` §6).
- Initialize **`todo.md`** and **`coding-standard/PROGRESS.md`** — both start empty;
  entries get added as work happens, per their own templates.

## 8. LICENSE and CITATION files

Add both at project root, one time, early — near-zero cost, real downside if skipped.

- **`LICENSE`**: no license file doesn't mean "no restrictions" — it defaults to "all
  rights reserved," meaning nobody (including a future collaborator, or you on a
  different machine six months from now) can legally reuse the code without asking.
  Recommended: CC-0 or CC-BY for data/text, a permissive license (MIT/BSD/Apache) for
  software. Avoid "noncommercial" restrictions — they block legitimate reuse in ways
  that aren't obvious upfront (e.g. a government researcher whose compiled report counts
  as commercial work in their institution). Avoid GPL for the same reason — permissive
  licenses are easier for others to integrate into their own projects.
- **`CITATION`**: states exactly how to cite the project, plus pointers to any
  separately-DOI'd data/code/figures. Ensures correct, consistent citation instead of
  ad hoc citation practices by whoever uses your work later.

## 9. What NOT to version-control

Add to `.gitignore` at setup time, not discovered by accident later:

- **Secrets and credentials** — the actual mechanism by which the README §4 stakes gate
  (`coding-standard/README.md`) gets violated in practice; this is the concrete
  `.gitignore` line that prevents it.
- **Raw data** — immutable by definition and regenerable from source; versioning it adds
  repo bloat for no benefit (exception: very small, text-based datasets where keeping
  them in-repo aids reproducibility more than it costs).
- **Anything over ~100MB** — git (and GitHub specifically) isn't built for large binary
  files; use external storage (S3, an experiment tracker's artifact store) instead.
- **Binary Office documents / PDFs** — git can store them but can't produce a meaningful
  diff between versions, which is the entire point of version control.

## 10. Optional: Makefile/DAG pipeline documentation

Recommended, not mandatory. Once `scripts/` grows past a couple of sequentially-
dependent driver scripts, a `Makefile` documents the dependency graph (what needs to
rerun when an input changes) and avoids redundant recomputation. Real server-based work
(SLURM jobs, shell-scripted pipelines) already covers much of the same "documented,
repeatable invocation" need — a Makefile is a genuine add-on for dependency-aware
regeneration on top of that, not a replacement for it.

```makefile
.PHONY: plot
plot: results/model.ckpt
	python scripts/generate_plots.py --ckpt results/model.ckpt --out results/figures/

results/model.ckpt: data/images
	python scripts/train.py --in_dir data/images --out_dir results/
```

Skip this section if the project's pipeline is simple enough that a shell script already
documents it adequately.
