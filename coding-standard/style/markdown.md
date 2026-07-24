# Markdown Style Decisions

Source: https://google.github.io/styleguide/docguide/style.html
Status: in progress — approved sections only, more to come.

## Philosophy

- [always] Prefer a small set of accurate, current docs over comprehensive-but-stale ones.
  Treat doc maintenance like test maintenance — if it's wrong, it's actively harmful, not
  neutral.
- [always] Prune stale docs opportunistically rather than in one big cleanup pass — delete/
  update in the same session where you notice the doc is wrong.
- [floor] Doc review bar is "reasonable," not "perfect" — don't block your own promotion on
  doc polish; fix the content, move on. Solo translation of "reviewer shouldn't block on
  nits": don't let a documentation pass become procrastination via polish.

## Layout

- [lib] Every promoted doc (README, spec, design doc) opens with: H1 title matching the
  filename, author/contributor attribution (keep this — collaborators may be involved and
  deserve credit), 1-3 sentence intro stating what the doc is and who it's for, then H2+
  content.
- [lib] Include a table of contents only when the doc is long enough, and structured enough
  (clear H2 sections), that a TOC actually helps navigation. Short docs or ones that read
  linearly top-to-bottom skip it. Reflection question: "would a reader jump to a specific
  section, or read this start to finish?" — jump-around docs get a TOC, linear ones don't.
- [always] Preserve correct capitalization of tool/library/product names (`PyTorch`, not
  `Pytorch`; `NumPy`, not `numpy` in prose — code identifiers still follow their own language
  convention).

## Formatting mechanics

No markdown formatter in use yet (manual as of 2026-07-23) — candidate: `mdformat` or
`prettier --parser markdown`, worth adopting later to make this section fully delegated
rather than self-enforced, same pattern as `ruff format` for Python (floor rule F4).

- [floor] 80-char soft wrap for prose paragraphs; exempt links, tables, headings, code
  blocks.
- [always] No trailing whitespace. Use a trailing `\` for an explicit line break instead of
  double-space (double-space is invisible and editors strip it silently).

## Headings

- [always] ATX style only (`#`/`##`/...), never underline-style.
- [always] Headings are unique and self-descriptive across the whole doc, even for repeated
  subsection patterns ("Design decisions" / "Design tradeoffs", not "Summary" reused per
  section) — this is what makes anchor links (`#foo-summary`) actually work.
- [always] One space after `#`; blank line before and after every heading.
- [always] Exactly one H1 per doc (the title); everything else H2 or deeper.

## Lists

- [floor] Use lazy numbering (`1.` for every item) for lists you expect to edit/reorder —
  most checklists and TODOs qualify. Use real sequential numbers only for short, stable
  lists (e.g. a fixed 3-step setup instructions block) where the numbers themselves carry
  meaning. Lazy numbering is what keeps a `todo.md` insertion from producing a diff that
  renumbers every following item.
- [always] Consistent nested-list indentation: 4 spaces per nesting level, so wrapped/nested
  content aligns under the marker text, not the marker itself.

## Code

- [always] Inline backticks for: short code fragments, field/variable names, file names,
  and any fake/example path or URL you don't want Markdown auto-linking.
- [always] Fenced code blocks over 4-space indentation, always — clearer, searchable, and
  lets you tag the language.
- [always] Every fenced block declares its language (`python`, `bash`, `json`, ...) —
  including for shell commands and config snippets, not just source files.
- [floor] Shell snippets meant to be copy-pasted use `\` to escape newlines so multi-line
  commands paste and run as one command.
- [always] Code blocks nested inside a list item are indented to the list's content indent,
  not the document margin.

## Links

- [always] Link titles are the natural phrase in the sentence, never "here"/"link"/"click
  this" — the link text itself should make sense read out of context (screen readers,
  link-list extraction tools).
- [floor] Use explicit repo-relative paths (`/path/to/page.md`) for links within this
  project's own docs; avoid `../`-style parent traversal since it breaks silently when
  files move.
- [floor] Use reference-style links (`[text][ref]`) when a URL is long enough to disrupt
  line wrapping, or reused more than once in the same doc. Short, single-use URLs stay
  inline.
- [always] Reference definitions go just before the next heading (footnote-style) unless
  the same reference is reused across multiple sections — then it goes at the document end.

## Images & Tables

- [floor] Use images sparingly — only when showing (a UI, a plot, a diagram) is genuinely
  clearer than describing. Every image gets alt text.
- [floor] Use tables only for uniform, parallel, multi-attribute data meant for quick
  scanning. If a table would have many empty cells or wildly uneven rows, restructure as
  headed lists instead (comes up in research notes more than you'd think — e.g. a results
  table where half the metrics don't apply to half the methods is usually better as
  per-method subsections).
- [floor] Keep table cells narrow — push long URLs out to reference links rather than
  inlining them in a cell.

## Prefer Markdown to HTML

- [always] Use plain Markdown syntax, not raw HTML, unless the content genuinely can't be
  expressed otherwise (Markdown's main gap is complex/large tables).

---

Status: complete — all 8 sections of the Google Markdown Style Guide processed and approved
(2026-07-23).
