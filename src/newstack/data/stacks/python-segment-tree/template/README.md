# {{ title }}

{{ description }}

A segment tree answers for windows, not for elements: every node of the
ladder holds the fold of its own span, a point edit re-folds only the
path it touched, and a query walks the ladder in a bounded number of
nodes. The combine function is the seam -- sum answers first, and the
same walk answers a minimum under a different fold.

## Why

A plain list answers a window by walking it, which costs the window.
The ladder answers in the ladder's depth: build folds the leaf row
upward once, `set` and `add` re-fold one path, and the query visits at
most twice the bit-length of the array. This tool exists to *show*
that, not to assert it:

```sh
$ {{ npm_name }} query --values fixtures/values.txt 3 10
```

Every claim below is a comparison the demo computes at run time, and
`selftest` refuses to pass when one stops holding.

## The six rules

1. **Every window answers exactly as its slice sums.** On seeded
   set/add/query storms, `query(lo, hi) == sum(values[lo:hi])` exactly
   -- the equality is the product.
2. **A rebuild from the leaf row equals the build it came from.** Same
   leaves in, same ladder out, fingerprint for fingerprint.
3. **A query visits at most `2 * n.bit_length()` nodes.** The visit
   count is printed with every answer, not waved away.
4. **A point edit re-folds only its path.** `set` lands, `add` slides,
   the pull-up follows, and the invariant is re-read after every move.
5. **Empty and full windows are honest.** The empty window answers the
   identity without a visit; the full window answers the total.
6. **The combine is the seam.** The same ladder walks under `min`, and
   the bound and the exactness survive the switch.

## Indexing

Public indices are **0-based** and windows are **half-open**:
`query(lo, hi)` covers `values[lo:hi]`, Python slice for slice.

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} demo
uv run {{ npm_name }} query --values fixtures/values.txt 3 10
uv run {{ npm_name }} set --values fixtures/values.txt 4 40
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `build [--values FILE] [--count N] [--seed S] [--mode sum\|min]` | load an array and print the ladder over it |
| `query [--values FILE] LO HI` | answer `[LO, HI)` and count the nodes visited |
| `set [--values FILE] INDEX VALUE` | drop a value on an index, re-fold the path |
| `add [--values FILE] INDEX DELTA` | slide an index by a delta, re-fold the path |
| `demo` | six stories about ladders and windows, with real numbers |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

`fixtures/values.txt` is one whole number per line, negatives allowed.
Blank lines and lines starting with `#` are skipped. Without `--values`
the array comes from the seeded generator instead (`--count`, `--seed`).

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the invariants hold |
| 1 | the window or index lies outside the array |
| 2 | the input cannot be read: a bad file, a bad value, a bad seed |

## Files

```
src/{{ package_name }}/tree.py        the ladder, the pull-up, the bound
src/{{ package_name }}/array.py       the whole numbers a window folds
src/{{ package_name }}/workload.py    seeded storms, replayed on the slices
src/{{ package_name }}/demo.py        six stories, every claim computed
src/{{ package_name }}/cli.py         the command line
src/{{ package_name }}/selftest.py    the invariants, runnable in a checkout
fixtures/values.txt                   an array the smoke test builds on
smoke.sh                              the tool driven the way a user drives it
```

## Non-goals

No floats, no lazy propagation, no range updates, no persisted storage,
no concurrent writers, no non-commutative order questions beyond the
half-open window itself. This is a tool for showing what a fold over a
ladder buys, not a replacement for a balanced-tree library.
