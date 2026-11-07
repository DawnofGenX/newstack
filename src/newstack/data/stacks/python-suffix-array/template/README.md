# {{ title }}

{{ description }}

A suffix is the text from one letter to the end: `banana` has six of
them, and the suffix array is their starting positions in the order a
plain `sorted(range(n), key=text[i:])` would answer with. The table
reaches that order by rank doubling — a sort per doubling round, an
honest O(n log^2 n) — and every answer it gives is checked against
the slice-sort, not against itself.

## Why

A table earns trust the only way a query structure can: its answers
must equal a dumb scan's, on every text, for every question. So this
tool exists to *show* that, not to state it:

```sh
$ {{ npm_name }} count --texts fixtures/texts.txt na
```

Every claim below is a comparison the selftest computes at run time
against the real modules, and `selftest` refuses to pass when one
stops holding. The falsifiable core is the scan: `scan.py` sorts by
slicing and counts by starting points with no structure at all, and
every order, count, share, and repeat the table returns must be the
identical answer.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the order is the plain sort | an array out of slice order | `array == sorted(range(n), key=text[i:])` on every seeded text |
| the count is every start | an entry point without the scan | `_window` scans forward from `bisect_left`; overlaps are counted per start, where `str.count` restarts after each match it spent |
| the shares sit between neighbours | an LCP array from the wrong pair | `lcp_array()` against the scan on every text, `lcp(i, j)` by the rank range |
| the repeat is the tallest share | a repeat the array cannot show | `longest_repeat()` against the scan's max share |
| empty and single letters answer | a complaint from the edges | the empty table, one-letter texts, a place past the end |
| the gate keeps letters in | digits, marks, uppercase, noise | the text gate section |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} build --texts fixtures/texts.txt
uv run {{ npm_name }} count --texts fixtures/texts.txt na
uv run {{ npm_name }} lrs --texts fixtures/texts.txt
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `build --texts FILE` | the sorted starts, the table itself |
| `count --texts FILE PATTERN` | every start holding the pattern, table order |
| `lrs --texts FILE` | the longest text repeated at two starts |
| `lcp --texts FILE I J` | letters the suffixes at I and J share |
| `demo` | six stories about starts and shares, with real numbers |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

`fixtures/texts.txt` is one lowercase text per line, letters `a`-`z`
only, up to one thousand twenty-four of them. Blank lines and lines
starting with `#` are skipped; the first text answers every question
in a run. A pattern is at least one letter — the empty pattern asks
for nothing and is refused by name.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the invariants hold |
| 1 | the pattern holds no start, the repeat is empty, the share is zero |
| 2 | the input cannot be read: a bad file, a bad text, a place past the end |

## Files

```
src/{{ package_name }}/suffix.py     the table, the doubling, the questions
src/{{ package_name }}/text.py       the gate the letters pass
src/{{ package_name }}/scan.py       the slice-sort that is the oracle
src/{{ package_name }}/corpus.py     text lists in, snapshots out
src/{{ package_name }}/workload.py   seeded storms, re-checked per answer
src/{{ package_name }}/demo.py       six stories, every claim computed
src/{{ package_name }}/cli.py        the command line
src/{{ package_name }}/selftest.py   the invariants, runnable in a checkout
fixtures/texts.txt                   a corpus the smoke test builds on
smoke.sh                             the tool driven the way a user drives it
```

## Non-goals

No uppercase, no digits, no punctuation, no text past one thousand
twenty-four letters, no sentinel character, no suffix-tree or LCE
shortcut, no persisted storage, no concurrent builders. The count
rule this text owes, written plain: occurrences are counted per start
position, so `aaaa` holds `aa` three times where `str.count` says two
— the table follows the scan, and the difference is documented, not
hidden. The table is the honest doubled-rank structure it is: a tool
for showing what sorted starts buy a text, not a replacement for
`sorted(range(n), key=text[i:])`.
