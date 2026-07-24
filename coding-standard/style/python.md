# Python Style Decisions

Source: https://google.github.io/styleguide/pyguide.html
Status: in progress — approved sections only, more to come.

## Language rules I: lint, imports, exceptions, global state

- [always] Run a linter (ruff is the modern pylint-equivalent) on every file — delegate
  mechanical bug-catching to the tool, same pattern as ShellCheck for shell.
- [floor] Suppress specific lint warnings inline with a reason comment; never blanket
  `# noqa` or disable a whole file. Unused args get `del arg1, arg2  # reason`, not silent
  neglect.
- [always] `import x` / `from x import y`; alias only for real collisions, real length
  problems, or a genuine standard abbreviation (`np`, `pd`, `nn` are fine — inventing your
  own abbreviation for an uncommon package is not). No relative imports.
- [always] Import by full package path — `import jodie` with no path context is a review
  flag, not just a style nit; it's actively hard to know where the symbol came from.
- [always] Built-in exception types used correctly (`ValueError` for bad args, etc.);
  never bare `except:` or blanket `except Exception` — the one exception is a deliberate,
  commented isolation boundary (e.g. don't let one failed run kill a whole sweep loop).
  Custom exceptions end in `Error`.
- [always] `assert` is for tests and internal invariants only — never for validating real
  preconditions on user-facing/callable code, since asserts are stripped under `-O` and
  silently vanish. Directly relevant to ML code: an assert checking a tensor-shape
  invariant is fine; an assert validating a CLI argument or config value is not — use
  `raise ValueError` there instead.
- [floor] Avoid mutable global state. Module-level constants (`ALL_CAPS`) are fine and
  encouraged. If mutable global state is genuinely needed (rare), it gets a leading
  underscore, public accessor functions, and a comment explaining why it has to be global
  rather than passed explicitly.

## Language rules II: comprehensions, generators, lambdas, defaults

- [always] Nested functions only when closing over a local value; don't nest purely to
  hide something from module users — use `_leading_underscore` at module level so tests
  can still reach it.
- [always] Comprehensions: one `for` clause, one filter, max. Anything needing nested
  loops or chained conditions becomes a real `for` loop — optimize for readability, not
  cleverness.
- [always] Use default iteration (`for k in adict`, `for line in afile`) not
  `.keys()`/`.readlines()`. Never mutate a container while iterating it.
- [floor] Generators: docstring says "Yields:" not "Returns:". If a generator holds an
  expensive resource (file handle, DB connection), wrap it in a context manager so cleanup
  happens even if the generator is abandoned before exhaustion.
- [always] Lambdas only for genuinely short single-expression cases; multi-line or long →
  a real named function (unreadable stack traces otherwise).
- [always] Ternary (`x if cond else y`) only when all three parts fit on one line;
  otherwise a real `if` statement.
- [always] Never a mutable object as a default argument value — defaults are evaluated
  once at module load, so `def f(x=[])` silently shares and mutates one list across every
  call. Use `def f(x=None): x = x if x is not None else []` instead. Classic, genuinely
  dangerous Python footgun — worth flagging in review specifically, not just trusting the
  linter, since it produces a plausible-looking bug that only shows up after multiple
  calls (a real "silent wrong results" case).
- [floor] `@property` only for real logic (access control, cheap derived values) — never
  as a pure pass-through with no computation. Don't use properties for anything a
  subclass might want to override.

## Language rules III: truthiness, scoping, decorators, threading, power features

- [always] Prefer implicit truthiness (`if foo:`), with hard exceptions: always
  `is None`/`is not None` for None-checks; never `== False` (`if not x:` instead); empty
  sequences are properly falsy (`if seq:` not `if len(seq):`); known-integer values get an
  explicit `== 0` comparison, since implicit falsy conflates `0` and `None`.
- [always] Numpy arrays / torch tensors: never rely on implicit bool context — multi-
  element arrays raise (`ValueError`/`RuntimeError`), so this fails loudly in a quick
  scalar test but can crash (or, via `mask or default`, silently take the wrong branch)
  the moment real batched data hits it. Use `.size`/`.numel()` explicitly
  (`if not arr.size:`), and never `x = x or default` when `x` might be an array — that
  forces truthiness evaluation on it. Use `is None` instead.
- [floor] Nested functions/closures capture the *variable*, not its value at definition
  time — a closure sees whatever the enclosing variable holds when it's *called*, not
  when it was *defined*. Concretely dangerous for per-layer hook registration: a hook
  defined inside a `for i, layer in enumerate(...)` loop that references `i` directly will
  have every hook read the *final* value of `i` once the loop ends, silently writing every
  layer's activation into the same slot. Fix: force eager capture via a default argument,
  `def hook(module, input, output, i=i): ...`. No error, no crash — just wrong data that
  looks structurally fine, which is exactly the "silent wrong results" failure mode.
- [floor] Decorators: never touch external resources (files, sockets, DB, network) inside
  a decorator body — they execute at import time, and a decorator failure is essentially
  unrecoverable. Never `@staticmethod` unless forced by an external API; use a
  module-level function instead. `@classmethod` only for named constructors or truly
  class-scoped state.
- [floor] Threading: don't rely on built-in-type atomicity (dict/list ops aren't
  guaranteed atomic in all cases); use `queue.Queue` for cross-thread data.
- [floor] Avoid metaclasses, bytecode/reflection tricks, dynamic inheritance, `__del__`
  cleanup — using library features built on these (`dataclasses`, `enum`, `abc.ABCMeta`)
  is fine, writing your own is not, except in rare justified cases.
- [always] `from __future__` imports: adopt as needed for newer syntax; don't remove one
  speculatively just because it looks unused right now — its presence guards against
  future edits silently depending on old behavior.
- [lib] Type annotations strongly encouraged, especially on anything crossing a module
  boundary (public functions, promoted library code). Full annotation conventions
  deferred to a dedicated pass (Cluster 8).

## Formatting mechanics

Enforced by an autoformatter (`ruff format`/`black`) where possible, but stated in full
here since this file should stand on its own.

- [always] No semicolons; never put two statements on one line.
- [always] 80-char line limit. Exceptions: long import lines, URLs/paths in comments,
  unsplittable long string constants (URLs/paths), pylint-disable comments. Docstring
  *summary* lines must stay under 80 even when the body doesn't. No backslash line
  continuation — use implicit joining inside `()`/`[]`/`{}` instead. Break at the highest
  syntactic level available; if a line needs breaking twice, break both at the same level.
- [always] Parentheses used sparingly — not around `if`/`while` conditions or `return`
  values unless needed for line continuation or to mark a tuple (`return (spam, beans)`
  is fine; `if (x):` is not).
- [always] 4-space indent, never tabs. Wrapped arguments/elements either align under the
  opening delimiter, or use a plain 4-space hanging indent with nothing on the first line.
  A closing bracket lines up with the indent of the line that opened it.
- [always] Trailing comma only when the closing bracket (`]`/`)`/`}`) is on its own line,
  or for a single-element tuple (`(foo,)`). This is also the signal that makes
  Black/Pyink lay the container out one item per line — add one deliberately to force
  that layout.
- [always] Two blank lines between top-level function/class definitions; one blank line
  between methods, and between a class docstring and its first method. No blank line
  immediately after a `def` line.
- [always] No whitespace inside `()`/`[]`/`{}`; no whitespace before `,`/`;`/`:` (but
  whitespace after, except at end of line); no whitespace before the opening paren/bracket
  of a call, index, or slice (`spam(1)` not `spam (1)`); no trailing whitespace.
- [always] Single space around binary/comparison/boolean operators (`=`, `==`, `<`, `and`,
  `or`, `not`, etc.); judgment call for arithmetic operators (`+`, `*`, `**`).
- [always] No spaces around `=` for keyword arguments or default parameter values
  (`f(x=1)`, `def f(x=1):`) — **except** when the parameter has a type annotation, where
  spaces around `=` are required instead (`def f(x: int = 1):`).
- [always] Never hand-align tokens vertically across consecutive lines (matching `=`
  signs, matching `:` in a dict) — it's a maintenance burden every future edit has to
  re-align.
- [floor] Shebang (`#!/usr/bin/env python3`) only on the directly-executed entry-point
  file, not on every module — Python ignores it on import, it only matters for direct
  execution.

## Comments & docstrings

- [always] `"""Triple double quotes"""` for all docstrings. Summary line ≤80 chars
  (same line-length rule as the rest of the file), ends in punctuation, blank line, then
  body at the opening-quote indent.
- [lib] Docstring required when a function is public API, non-trivial, or has non-obvious
  logic — this is the comment-as-API-contract principle: someone should be able to call
  the function correctly from the docstring alone, without reading the body.
- [lib] No hard length cap on the docstring body — a docstring with many parameters or
  real behavioral nuance (e.g. a training entrypoint with five config args, or a function
  documenting why a particular numerical approximation is used) is expected to run long,
  and every line should earn its place. What's discouraged is padding — restating the
  obvious, or explaining implementation detail nobody calling the function needs. This is
  distinct from `#` inline/block comments below, which do stay short — a docstring is a
  reference consulted once before calling; a `#` comment is read inline while scanning.
- [lib] Structured sections when useful: `Args:` (name + description per param),
  `Returns:`/`Yields:` (semantics beyond what the type annotation already says — omit for
  `None` returns), `Raises:` (exceptions from the function's own logic, not generic
  misuse). Omit sections entirely for functions the name+signature already fully explain.
- [floor] Module docstring: one-line summary + description, required for real modules.
  Test-file modules: skip unless there's something non-obvious to say (unusual setup,
  external dependencies) — an empty-of-content docstring is worse than none.
- [lib] Class docstrings: one-line summary of what an *instance* represents (not "Class
  that..." framing), plus an `Attributes:` section for public non-property attributes.
  Exception classes describe the error condition itself, not "raised when."
- [always] Block/inline (`#`) comments are for tricky, non-obvious sections only — never
  restate what the code does. Why-not-what discipline (reflect before writing one, keep
  it short — roughly 5 lines, not a paragraph) applies here specifically, not to
  docstrings.
- [always] `#` starts ≥2 spaces after code, ≥1 space after `#`. Comment prose gets normal
  capitalization/punctuation — reads like a sentence, not a fragment, except short
  end-of-line notes where brevity is fine as long as it's consistent within the file.

  ```python
  # We interpolate between baseline and input rather than backpropping through
  # `inputs` directly, because a single gradient at the input point is a poor
  # approximation when the model is highly nonlinear near that point.
  if baseline is None:
      baseline = torch.zeros_like(inputs)
  ```

## Strings, resources, TODOs, imports, statements

- [always] f-strings/`%`/`.format()` all fine — pick what's clearest for the case. Never
  accumulate a string with repeated `+=` in a loop (quadratic) — build a list and
  `''.join()`, or use `io.StringIO`.
- [always] Pick `'` or `"` and stay consistent within a file; switch only to avoid
  escaping. `"""` required for docstrings; prefer it for other multi-line strings too.
  Use `textwrap.dedent()` for indented multi-line string literals rather than letting
  leading whitespace leak into the string value.
- [always] Logging calls: pass the pattern string as a literal with `%s` placeholders,
  never a pre-formatted f-string — `logging.info('Value: %s', x)` not
  `logging.info(f'Value: {x}')`. Some backends skip rendering entirely when not
  configured to emit that level; eager formatting wastes the work and defeats that.
- [always] Error messages: the condition checked must exactly match the condition
  described (watch for NaN/edge cases silently slipping past a `<`/`>` check that a
  `0 <= x <= 1`-style check would catch); mark interpolated values explicitly
  (`f'{p=}'`); don't editorialize about *why* something failed unless you've actually
  verified the reason — state what you know, not what you're guessing.
- [always] Any stateful resource (files, sockets, DB connections, `mmap`, `h5py.File`,
  `matplotlib` figure windows) gets explicit `with` (or `contextlib.closing()` if it
  doesn't support `with` natively) — never rely on garbage collection to close it.
- [always] TODO format: `# TODO: <link> - description`, where `<link>` is a resolvable
  reference, never a person's name. For this standard, `<link>` points to the todo.md
  entry it corresponds to (e.g. `# TODO: todo.md#T014 - handle empty batch case`) —
  keeps a TODO comment and its priority/status in todo.md as one traceable pair rather
  than two disconnected records. (Reconciles with the Shell guide's TODO format —
  see shell.md, Comments section.)
- [always] One import per line (`typing`/`collections.abc` may share). Import order:
  `__future__` → stdlib → third-party → local sub-packages, alphabetical within each
  group, imports placed after the module docstring and before any module constants.
- [always] One statement per line. The only exception: a bodyless `if foo: bar(foo)` that
  fits on one line — never for `if/else`, never for `try/except`.

## Getters/setters & naming

- [floor] `get_foo()`/`set_foo()` only when the operation is non-trivial (expensive, or
  invalidates/rebuilds state). A getter/setter that's a pure pass-through to an internal
  attribute should just be a public attribute — no wrapper. If replacing a `@property`
  with real accessor methods, let old call sites break loudly rather than silently
  rebinding the property name to the new methods.
- [always] Descriptive names; no ambiguous/unfamiliar abbreviations, no deleting letters
  mid-word to shorten something. Files: `.py`, never dashes.
- [always] Single-character names only for: loop counters (`i`, `j`, `k`), `e` in
  `try/except`, `f` for a `with`-block file handle, unconstrained private `TypeVar`s, and
  names matching established paper/algorithm notation (see Mathematical Notation, next
  section). Scale descriptiveness to scope — `i` is fine in a 5-line block, not buried in
  nested scopes.
- [always] Avoid: dashes in package/module names, `__dunder__` names (reserved by
  Python), and type-redundant names (`id_to_name_dict` when the type is already visible).
- [always] Single leading underscore (`_foo`) for internal/protected — linter-enforced,
  still reachable by tests. Avoid double leading underscore (`__foo`) — triggers real
  name-mangling, isn't truly private, and hurts testability. Prefer single underscore.
- [always] `CapWords` for classes and exceptions; `lower_with_under` for everything else
  (modules, functions, variables, parameters), full table:

  | Type | Public | Internal |
  |---|---|---|
  | Packages | `lower_with_under` | |
  | Modules | `lower_with_under` | `_lower_with_under` |
  | Classes | `CapWords` | `_CapWords` |
  | Exceptions | `CapWords` | |
  | Functions | `lower_with_under()` | `_lower_with_under()` |
  | Global/Class Constants | `CAPS_WITH_UNDER` | `_CAPS_WITH_UNDER` |
  | Global/Class Variables | `lower_with_under` | `_lower_with_under` |
  | Instance Variables | `lower_with_under` | `_lower_with_under` (protected) |
  | Method Names | `lower_with_under()` | `_lower_with_under()` (protected) |
  | Function/Method Parameters | `lower_with_under` | |
  | Local Variables | `lower_with_under` | |

- [always] Test methods: `test_<method_under_test>_<state>`. `test<MethodUnderTest>_<state>`
  allowed when the method under test is itself `CapWords`-named (legacy consistency).

## Mathematical notation

- [floor] Short, paper-matching variable names (`W`, `x`, `h_t`, `theta`, `Q`, `K`, `V`)
  are preferred over descriptive names inside math-heavy code (loss functions, attention
  mechanisms, gradient computations, attribution formulas) *when they match an actual
  established notation* — not as a general license for terse naming.
- [always] Every time notation-matching short names are used, cite the source right
  there: a comment or docstring line linking to the paper/section the notation comes
  from. Undocumented short names in math code are a review-flaggable naming violation,
  not an accepted exception — the citation is what makes the exception valid.
- [always] Public API surface (anything called from outside the file/module — a
  function signature other code imports and calls) uses descriptive names even in
  math-heavy code, regardless of what notation the internals use. The notation exception
  applies to internal computation, not to what callers see.
- [floor] Suppress the linter's `invalid-name` warning narrowly — per-variable endline
  comment (`W = ...  # pylint: disable=invalid-name`) for a few names, or a block-level
  directive at the top of a function/section when there are many. Never a whole-file
  suppression for this.

  ```python
  def scaled_dot_product_attention(
      query: torch.Tensor, key: torch.Tensor, value: torch.Tensor
  ) -> torch.Tensor:
      """Computes attention per Vaswani et al. 2017, eq. 1.

      https://arxiv.org/abs/1706.03762

      Notation matches the paper: Q, K, V for query/key/value, d_k for the
      key dimension.
      """
      # pylint: disable=invalid-name
      Q, K, V = query, key, value
      d_k = K.shape[-1]
      scores = Q @ K.transpose(-2, -1) / math.sqrt(d_k)
      return torch.softmax(scores, dim=-1) @ V
  ```

## Main & function length

- [floor] Any file meant to be run directly wraps its real logic in `main()`, gated by
  `if __name__ == '__main__':` — nothing at module top-level should have side effects
  (function calls, object construction with real cost) that would fire just from being
  imported, since import always executes top-level code.
- [floor] No hard function-length cap, but ~40 lines is the threshold to actively ask "can
  this split without harming structure?" The risk isn't current readability — it's that a
  long function accumulates behavior over time as it gets modified later, and the bugs
  that introduces are harder to find in a large function than a small one. Same
  underlying concern as the Sandi Metz wrong-abstraction pattern (reading-notes, Round 1):
  a function that's grown past its original scope by accretion is a candidate for the
  same inline-and-rederive treatment, not further patching.
- [always] Don't be deterred from splitting up an existing long/complicated function you
  didn't write (or wrote a while ago) just because it currently works — if it's hard to
  debug, or you need one piece of it reused elsewhere, that's the signal to break it up.

## Type annotations I: general rules, forward refs, None, aliases

- [lib] Annotate selectively, prioritized: public APIs first, then error-prone/complex
  logic, then mature/stable code. Don't chase 100% annotation coverage uniformly —
  annotate where it earns its keep (catching real type errors, documenting a non-obvious
  interface), not as a checkbox exercise. Skip `self`/`cls`/`__init__`'s return type
  (always implicitly `None`). Use `Self` for classmethods returning an instance or
  methods comparing against another instance of the same class. `Any` when a type
  genuinely can't/shouldn't be expressed.
- [lib] Annotated signatures naturally go one-parameter-per-line when they get long;
  trailing comma after the last param to give the return type its own line. Break the
  *type itself* across lines only as a last resort — alias an overly long type instead.
- [lib] Self-referencing/forward-referenced classes: `from __future__ import annotations`
  (defers all annotation evaluation) or a quoted string literal (`"MyClass"`).
- [always] Spaces around `=` for a default value only when the parameter also has a type
  annotation (`def f(a: int = 0)`); no spaces without one (`def f(a=0)`).
- [always] `None`-ability must be declared explicitly (`x: str | None`), never left
  implicit just because the default value happens to be `None`. Modern union syntax
  (`X | None`) preferred over `Optional[X]` in new code.
- [lib] Complex or repeated types get a `CapWords` type alias with `: TypeAlias`
  (`_LossAndGradient: TypeAlias = tuple[Tensor, Tensor]`); leading underscore for
  module-private aliases, matching general naming conventions.
- [floor] `# type: ignore` to disable checking on a specific line — narrow, not a whole
  file. pytype-specific issues use `# pytype: disable=<check>` instead of the generic form.
- [always] For variables a type checker can't infer, annotate the assignment directly
  (`a: Foo = some_call()`). Never the old `# type: Foo` trailing-comment syntax — dead
  pre-3.6 convention, shouldn't appear in new code.

## Type annotations II: containers, type vars, imports, generics

- [lib] `list[T]` for a single-type collection; `tuple[T, ...]` for a repeated-type
  tuple; `tuple[T1, T2, T3]` for a fixed heterogeneous tuple — the idiomatic way to type
  a multi-value function return.
- [lib] `TypeVar`/`ParamSpec` for generics; constrain a `TypeVar` to a specific type set
  when appropriate (`TypeVar("AddableType", int, float, str)`); `AnyStr` when a function
  must be consistently `bytes`-in/`bytes`-out or `str`-in/`str`-out. Type variables need
  a real descriptive name unless both unexported and unconstrained (`_T`/`_P` fine only
  in that narrow case — a constrained var always gets a real name).
- [always] `str` for text, `bytes` for binary. Never `typing.Text` — dead Python 2/3-compat
  syntax, shouldn't appear in new code.
- [always] Import typing symbols directly (`from typing import Any, cast`), multiple per
  line is fine; treat these names as reserved, don't shadow them; alias on collision.
  Prefer abstract container types in signatures (`Sequence`) over concrete ones (`list`)
  unless a concrete type is genuinely required — and then prefer the builtin (`tuple`)
  over the deprecated `typing.Tuple`.
- [floor] Conditional imports (`if TYPE_CHECKING:`) only for the narrow case of an
  import needed purely for type-checking that must not run at runtime — prefer
  refactoring to a normal top-level import first. If used: string-literal reference in
  the annotation, placed right after normal imports, no blank lines inside the block,
  sorted normally.
- [floor] A circular dependency caused by type annotations is a refactor signal, not
  something to route around indefinitely — if it must be kept short-term, alias the
  problem module to `Any` rather than actually importing it.
- [always] Always specify a generic's type parameters explicitly (`Sequence[int]`, not
  bare `Sequence`) — an unparameterized generic silently becomes `Sequence[Any]`, which
  defeats the point of annotating. If `Any` really is correct, write it explicitly; but
  consider whether `TypeVar` is the more accurate choice first.
- [floor] Types unavailable in the current Python version: import under
  `if TYPE_CHECKING:`. Code needing very old Python support can use string-literal
  forward references instead of pulling from `typing_extensions`.

## Closing principle

- [always] Consistency within a project matters, but a style rule that genuinely doesn't
  fit the situation should be deliberately overridden, not silently followed out of
  habit — when in doubt, that's worth a conscious call, not a default.

---

Status: complete — all 11 clusters of the Google Python Style Guide processed and
approved (2026-07-23).
