# Shell Style Decisions

Source: https://google.github.io/styleguide/shellguide.html
Status: in progress — approved sections only, more to come.

## When (and which) shell

- [always] `#!/bin/bash` for every executable script — no POSIX-sh, no zsh-specific
  syntax. Bashisms are fine and expected since bash is the only target.
- [floor] Shell is for thin wrapper/utility scripts — orchestrating other commands, light
  data shuffling. The moment a script crosses ~100 lines or needs real control flow
  (nested conditionals, data structures, error handling beyond exit codes), stop and
  rewrite it in Python instead of continuing to grow it in bash.
  Reflection question: "if future-me had to debug this at 2am, would bash's error
  messages be enough, or would I want a real stack trace?" — that's usually the tell for
  when a script should have been Python from the start.

## File conventions

- [always] Executable scripts: `.sh` extension, or no extension if meant to be called
  directly (e.g. placed on PATH or run as `./script`). Sourced/imported libraries: `.sh`
  extension, not executable.
- [always] Never SUID/SGID a shell script. Use `sudo` for anything needing elevated
  privileges.
- [always] Errors go to STDERR, never STDOUT. Use a shared `err()` helper instead of raw
  `echo` for any error message:

  ```bash
  err() {
    echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')]: $*" >&2
  }

  if ! do_something; then
    err "Unable to do_something"
    exit 1
  fi
  ```

  The `>&2` is the load-bearing part — it's what keeps error text out of STDOUT. This
  matters concretely: if a script's normal output is captured (`result=$(script.sh)`) or
  piped downstream, an un-redirected `echo` error silently mixes into that captured
  output — a real "silent wrong result" risk, since a downstream step may treat the error
  text as legitimate output and not realize the run failed.

## Comments

- [always] File header: 1-2 lines at the top describing what the script does.
- [lib] Any non-trivial or non-obvious function gets a header comment with: Description,
  Globals used/modified, Arguments, Outputs, Returns (non-default exit codes) — matches
  the comment-as-API-contract decision already made for general code (see reading-notes
  decisions.md, Round 10): someone should be able to call the function correctly from the
  comment alone.
- [always] Implementation comments only for genuinely tricky/non-obvious logic — same
  why-not-what discipline as Round 10, not a separate rule here.
- [always] TODOs: `# TODO: <link> - description` format, where `<link>` points to the
  matching todo.md entry (e.g. `# TODO: todo.md#T014 - handle empty input`), not a
  person's name — matches Python's reconciled TODO format (see
  python.md, "Strings, resources, TODOs..." section). Ties into the
  existing todo.md system (Round 12): the comment and its priority/status live as one
  traceable pair, not two disconnected records.

## Formatting

- [always] 2-space indent, no tabs (heredoc-body exception noted, rarely relevant).
- [always] 80-char line limit; long literal strings go in a heredoc or embedded newline,
  not one long line. Unsplittable long tokens (paths, URLs) go on their own line or into
  a variable rather than forcing a line over the limit.
- [always] Pipelines: single line if it fits; otherwise one command per line, leading pipe,
  2-space indent, `\` continuation. Same treatment for `||`/`&&` chains.
- [always] `; then`/`; do` on the same line as the opener; `else`, `fi`, `done` on their own
  aligned lines. Always write `for x in "$@"; do` explicitly, never rely on the implicit
  form.
- [always] `case` bodies indented one level from `case`/`esac`; multiline actions indented
  one further level. Short one-liners inline are fine for simple option parsing.

## Variables & quoting

- [always] Brace-delimit variables (`"${var}"`), except bare single-character specials/
  positional params (`$1`, `$?`, `$!`) where bracing adds no clarity.
- [always] Quote every variable and command substitution by default (`"${var}"`,
  `"$(cmd)"`) unless unquoted expansion is a deliberate, understood choice (rare — usually
  glob expansion or intentional word-splitting).
- [always] Use arrays for any list of things passed as arguments (especially CLI flags) —
  never build a flag list as a single space-joined string. A joined string reliably breaks
  the moment an argument contains a space.

  ```bash
  # Do this:
  declare -a flags
  flags=(--foo --bar='baz')
  flags+=(--greeting="Hello ${name}")
  mybinary "${flags[@]}"

  # Not this — breaks the moment an arg has a space in it:
  flags='--foo --bar=baz'
  flags+=' --greeting="Hello world"'
  mybinary ${flags}
  ```

- [always] Use `"$@"` to forward arguments, essentially never `$*` — `"$@"` preserves each
  argument as a distinct word (including ones with embedded spaces); `$*` and unquoted
  `$@` silently mangle them via word-splitting. Classic failure mode: works fine in testing
  because your test paths have no spaces, breaks on a real path that does.

## Correctness tooling & common bugs

- [always] Run ShellCheck on every script before it's considered done — catches real
  correctness bugs, not just style. Treat it like `ruff` for Python (F4-equivalent):
  delegate to the tool, don't hand-check for the things it already covers.
  **Wired into CODE_REVIEW.md**: `shellcheck` runs automatically as part of the review
  workflow's setup/automated-checks step for any shell file in the change, before the
  manual review sections start — a clean ShellCheck pass is a precondition for review,
  not something the reviewer (human or agent) has to remember to run separately.
- [always] `$(command)` for substitution, never backticks.
- [always] `[[ … ]]` for tests, never `[ … ]`/`test`. Use `-z`/`-n` for empty/non-empty
  checks, `==` for string equality, `(( … ))` or `-lt`/`-gt` for numeric comparison — `<`/
  `>` inside `[[ ]]` are lexicographic, a real trap (`[[ 4 > 22 ]]` is true).
- [always] Wildcard-expand with an explicit path (`./*`, not bare `*`) — a bare `*` can
  hand filenames starting with `-` to a command as if they were flags, with destructive
  results (`rm -v *` can be tricked into deleting more than intended by a `-f`-named file).
- [always] Never use `eval` — it obscures what's actually executed and breaks reliable
  exit-code checking. If you're reaching for `eval`, that's a signal to restructure the
  script (often into arrays, see next section) rather than work around it.

## Arrays, loops, arithmetic, aliases

- [always] Use arrays for argument lists; never build a flag/argument list as a joined
  string (ties to the Variables & Quoting section above). Arrays are for lists, not
  complex data structures — needing the latter is a "this should be Python now" signal.
- [always] Never assign command output directly into an array with unquoted expansion
  (`files=($(ls ...))`) — goes through word-splitting/globbing first and silently
  mishandles filenames with spaces/special characters. Use `readarray`/`mapfile` instead.
- [always] Prefer process substitution (`< <(cmd)`) or `readarray` over piping into
  `while` — a `while` fed by a pipe runs in a subshell, so any variable set inside the
  loop silently reverts once the loop ends. This is exactly the "silent wrong results"
  failure mode the whole standard is built around: the script produces a plausible-looking
  final value with zero error output, and it's simply wrong.
- [always] Arithmetic: `(( … ))`/`$(( … ))` only — never `let`, `$[ … ]`, `expr`. Caution:
  don't use `(( … ))` as a bare standalone statement under `set -e` — if it evaluates to
  0, the script exits (e.g. `(( i++ ))` when `i` starts at 0 triggers this).
- [always] No aliases in scripts — use a function instead. Aliases are fine in an
  interactive `.bashrc`, not in anything that runs non-interactively.

## Naming & structure

- [always] Functions and variables: `lowercase_with_underscores`; library functions use
  `package::function`. No space before `()`. Loop variables named for what they iterate
  (`for zone in "${zones[@]}"`, not `for i in ...`).
- [always] Constants and exported env vars: `ALL_CAPS_WITH_UNDERSCORES`, declared at the
  top of the file. Runtime-computed constants are fine — mark `readonly` immediately after
  computing, don't leave a window where it's mutable-but-should-be-fixed.
- [always] Function-local variables: always `local`. Critical gotcha —
  `local var="$(cmd)"` masks the command's real exit code with `local`'s own (always 0).
  Split into two statements whenever the exit code matters:
  ```bash
  local my_var
  my_var="$(my_func)" || return
  ```
- [floor] All functions declared together near the top of the file, below constants,
  before any top-level executable code — no logic interleaved between function defs.
- [floor] Any script with more than one function wraps its top-level logic in `main()`,
  called as the literal last line (`main "$@"`). Skip `main` for genuinely short, linear
  scripts — this isn't worth the ceremony below a certain size.

## Command results & consistency

- [always] Check the return value of every command that can fail, with an informative
  message on failure (routed through `err()`, per the File conventions section above).
- [floor] For pipelines where you need to know *which* stage failed, capture
  `"${PIPESTATUS[@]}"` into a variable immediately — it gets clobbered by the very next
  command, including `[`/`[[`, so there's no "check it later."
- [always] Prefer bash builtins (parameter expansion, `(( … ))`, `=~`) over spawning
  external tools (`sed`, `expr`, `grep` for simple string ops) when a builtin does the
  same job — faster, and avoids the subprocess-quoting bugs external calls invite.
- [floor] When a rule is genuinely ambiguous and no clear technical reason favors one
  option, match whatever's already in the file. This is a tiebreaker only — it's not a
  reason to keep something worse than what you now know to be better.

---

Status: complete — all 9 sections of the Google Shell Style Guide processed and approved
(2026-07-23).

  ```bash
  # "$@" retains each argument as-is — this is what you want almost always.
  forward_args() {
    some_command "$@"
  }

  # $* joins everything into one string — usually wrong for forwarding arguments,
  # only appropriate for something like a log message.
  log_call() {
    echo "called with: $*"
  }
  ```
