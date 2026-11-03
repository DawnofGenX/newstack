# Contributing

Thanks for taking a look. This project is small on purpose: a standard-library CLI plus a
registry of templates, so a change is usually one of two things — a fix to the CLI, or a
new/fixed stack.

## Setup

```bash
git clone https://github.com/DawnofGenX/newstack
cd newstack
uv sync --group dev
uv run pytest
uv run newstack list
```

## The one rule

**A stack is not done until `newstack check <stack>` passes on a clean machine.**

If you add or change a stack, run:

```bash
uv run newstack check <stack> --verbose
```

and commit only when it reports `PASS`. The same command runs in CI, once per stack; a
red template is a red build.

## Adding a stack

1. `mkdir -p src/newstack/data/stacks/my-stack/template`
2. Write `stack.json` next to `template/` (see the table in the README for fields).
   The `name` field must match the directory name.
3. Put the files in `template/`. Use `{{ variable }}` placeholders.
4. Add verification steps to `stack.json` — at minimum install and test.
5. Add the `adopt` allow-list (and optional `detect` rules) so `newstack adopt` knows what
   infrastructure this stack owns. Adopt lists may contain only infra paths that exist in
   `template/`; identity files are rejected by a test.
6. `uv run newstack check my-stack` until it is green.

Templates are also the input to `newstack update`, which re-renders them into projects
users already generated. So keep a template free of state that only makes sense once —
`newstack new` records what it wrote, and every later run of that template is merged
against the record, file by file.

Available template variables: `project_name`, `package_name` (python-safe, `snake_case`),
`npm_name` (npm-safe, `kebab-case`), `title`, `description`, `author`, `email`, `year`,
`date`, `stack`, `stack_title`, `newstack_version`.

Two escapes exist so that templating does not fight the code you generate:

- `{{!` emits a literal `{{`.
- `${{ … }}` is left untouched, so GitHub Actions expressions survive rendering.

## Code rules

- Standard library only — no runtime dependencies, ever.
- `uv run ruff check .` and `uv run pytest` must be clean.
- New CLI behaviour needs a test that fails without the change.

## GitHub Actions refs in templates

Pin actions to a tag that actually resolves. `actions/*` publish moving major tags
(`@v7`), so those are fine. `astral-sh/setup-uv` publishes **only exact tags** — use
`@v10.3.3`, never `@v10`; an unresolvable ref fails the whole job at "Set up job".
`tests/test_stacks.py` enforces this.

## Reporting problems

Open an issue with the output of `newstack doctor` and `newstack check <stack> --verbose`.
That usually contains everything needed to reproduce.

## Demo conventions

Every user-facing stack ships a small demo so a fresh project proves itself on first run.
Two rules keep those demos from drifting apart:

- **Counter demos persist.** If a stack shows a counter, it stores the value under the
  single key `newstack:counter`, clamps stored values to a non-negative integer, and
  restores after mount when the framework renders on the server. `chrome-extension` uses
  `chrome.storage.local` with the same key and the same clamping. `tests/test_stacks.py`
  enforces the key.
- **State is never the label.** A control says what it *does* ("Increment"); the current
  value lives in a separate element with `role="status"` so a screen reader hears the
  change rather than a button renaming itself.
