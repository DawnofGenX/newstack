# {{ title }}

{{ description }}

An MkDocs Material site that documents a tiny `wc`-style counting module — and
proves the documentation is still true. `tools/check_fences.py` runs every
`python` fenced example in `docs/` and compares the printed output with the
`# ->` lines next to it, so an example that no longer matches the module fails
CI instead of shipping.

## Layout

```
mkdocs.yml                site config: Material theme, nav, Markdown extensions
docs/index.md             landing page with an executed example
docs/guide/counting.md    the rules, one executed example per rule
docs/reference/api.md     API reference with an executed example
src/{{ package_name }}/counters.py   the module the site documents
tools/check_fences.py     executes the fenced examples and diffs their output
tests/                    counting rules, the checker's own contract, and the built site
```

## Commands

```bash
uv sync --group dev
uv run mkdocs serve          # http://127.0.0.1:8000
uv run mkdocs build --strict # the CI gate: any warning fails the build
uv run python tools/check_fences.py docs
uv run pytest
```

## Writing an example

````markdown
```python
from {{ package_name }} import count_text

print(count_text("hello world\n"))
# -> Counts(lines=1, words=2, bytes=12)
```
````

Every `# ->` line is expected standard output; everything else in the fence is
code. Blocks on one page share a namespace, so a later block can use a name an
earlier one defined. A fence with no `# ->` lines is only checked for
exceptions.

`mkdocs build --strict` and the fence checker catch different mistakes: `--strict`
catches broken internal links, missing nav entries and unrecognised Markdown
config; the checker catches documentation that no longer describes the code.
