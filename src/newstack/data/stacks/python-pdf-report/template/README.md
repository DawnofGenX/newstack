# blog-report — deterministic PDF reports of text statistics

Reads NDJSON (one `{"id": …, "text": …}` per line), counts lines, words and UTF-8
bytes per record, and renders a PDF with a table, a totals line and page numbers.
The point is not the layout — it is that the same input produces the same bytes, and
that the numbers on the page are the numbers that were counted.

```bash
uv venv --allow-existing .venv
uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m {{ package_name }}.cli --input fixtures/records.ndjson --output report.pdf --json
.venv/bin/python -m pytest -q
bash smoke.sh
```

```
src/{{ package_name }}/counts.py   line/word/byte counting over raw UTF-8 bytes
src/{{ package_name }}/model.py    NDJSON parsing, with errors that name the line
src/{{ package_name }}/render.py   reportlab platypus build; invariant + font sanitising
src/{{ package_name }}/cli.py      argparse, stdin/stdout, JSON summary
tests/test_report.py   counts, parsing, determinism, and the PDF read back
```

## Traps this starter already paid for

1. **`rl_config.invariant = 1` must be set before the first canvas exists.** ReportLab
   stamps `/CreationDate` from the wall clock and generates random object ids, so two
   runs of the same input produce different bytes. With `invariant` the date is pinned
   to `D:20000101…` and the report becomes diffable and cacheable — the test asserts
   the fixed date, because a wall-clock stamp would silently re-enter the bytes.
2. **The built-in Type1 fonts are WinAnsi (≈ cp1252).** Anything outside that range is
   drawn as a black box and extracts as garbage, with no warning from ReportLab. Every
   character is checked against `cp1252` before it is placed, replaced with `?`, counted,
   and reported on the page and on stderr. A report that quietly drops characters looks
   finished and is wrong.
3. **`count_text` counts newline characters, not "lines of output".** `"a b\nc\n"` is
   2 lines; `\r` is a word separator and not a line break, which is why CRLF text does
   not double-count.
4. **Bytes are not characters.** `"héllo wörld\n"` is 12 characters and 14 bytes; the
   test asserts both numbers so a refactor to `len(text)` fails loudly.
5. **Reading the PDF back is the only proof the numbers reached the page.** A summary
   computed in the process can be perfectly right while the layout drops the table; the
   smoke test extracts text with `pypdf` and greps for the rows and the totals line.
6. **A refused input must leave no PDF behind.** The document is built in memory and the
   file is written only after a successful build, so exit code 2 cannot leave a
   half-written report that a later step happily uploads.
7. **NDJSON errors carry the line number and nothing is skipped silently.** Dropping a
   malformed record from a report is worse than refusing to build it.
8. **`pip install -e .` before `src/{{ package_name }}/` exists installs nothing.** Hatchling happily
   builds an empty wheel from just the `pyproject.toml`, and the next `python -m {{ package_name }}.cli`
   dies `ModuleNotFoundError: No module named 'report'`. Write the package first, then
   install; the install step is idempotent either way.
9. **`document.page` is only meaningful after `build()`.** Page counts come from the
   template object after rendering, not from an estimate of rows per page.
10. **`mktemp -d` plus a trap in `smoke.sh`.** The smoke run writes three PDFs; without
    the trap they land in the working tree and the next `git status` is a puzzle.
