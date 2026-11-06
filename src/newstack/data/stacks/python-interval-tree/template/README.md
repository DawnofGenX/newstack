# {{ title }}

{{ description }}

An interval tree stores half-open spans `[start, end)`: a point inside a span
satisfies `start <= point < end`, so the right end never belongs to the span
it ends. Each node also remembers the highest end in its subtree — the
max-end augmentation — and a stabbing or overlap query reads that one number
to skip whole subtrees it cannot answer from.

## Why

An interval tree earns trust the only way a query structure can: its answers
must equal a dumb linear scan's, on every corpus, after every delete. So this
tool exists to *show* that, not to state it:

```
$ {{ npm_name }} stab --intervals fixtures/spans.txt --point 5
```

Every claim below is a comparison the selftest computes at run time against
the real modules, and `selftest` refuses to pass when one stops holding. The
falsifiable core is the scan: `scan.py` walks the whole corpus with one
comparison per span, and every stabbing and overlap answer the tree returns
must be the identical list, in the identical order.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the scan is the oracle | a stabbing or overlap answer that misses or invents a span | every seeded corpus in the selftest and the tests |
| half-open spans | a stab at `end` counted inside the span it ends | the boundary section, `holds` and `overlaps` |
| the augmentation is live | a `max_end` that a delete left stale | `audit()` after every delete in the selftest |
| ordering is the walk | a walk out of `(start, end)` order | `walk()` against `sorted()` on every corpus |
| deletion rewrites heights | a subtree skipped because its parent remembers too little | `_retrace` coverage in the delete loop |
| an empty tree answers | a crash or a complaint before the first insert | the empty-tree section |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} load --intervals fixtures/spans.txt
uv run {{ npm_name }} stab --intervals fixtures/spans.txt --point 5
uv run {{ npm_name }} overlap --intervals fixtures/spans.txt --low 2 --high 8
uv run {{ npm_name }} first --intervals fixtures/spans.txt --point 5
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `load --intervals FILE [--json]` | build the tree and walk every span in order |
| `stab --intervals FILE --point N [--json]` | every span holding this point, ascending |
| `overlap --intervals FILE --low N --high N [--json]` | every span touching `[low..high)` |
| `first --intervals FILE --point N [--json]` | the earliest-starting span holding the point |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

`fixtures/spans.txt` is two integers per line: `start end`. Blank lines and
lines starting with `#` are skipped. Spans are half-open — `start` counts,
`end` does not — and must satisfy `start < end`.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was found, or the invariants hold |
| 1 | no span answers: the point is held by nothing, the window touches nothing |
| 2 | the input cannot be read: a bad file, an empty span, an inverted window |

## Files

```
src/{{ package_name }}/span.py        the half-open span: holds, overlaps
src/{{ package_name }}/tree.py        the tree, the augmentation, the queries
src/{{ package_name }}/scan.py        the brute-force oracle every answer faces
src/{{ package_name }}/corpus.py      span lists and a deterministic generator
src/{{ package_name }}/cli.py         the command line
src/{{ package_name }}/selftest.py    the invariants, runnable in a fresh checkout
fixtures/spans.txt                    a corpus the smoke test walks
smoke.sh                              the tool driven the way a user drives it
```

## Non-goals

No floating-point endpoints, no closed or open ranges, no duplicate-tracking,
no persistence, no concurrent writers. This is a tool for showing where an
interval tree keeps its promises — stabbing and overlap equal to the scan,
augmentation alive after every delete — not a database index.
