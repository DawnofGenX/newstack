# {{ title }}

{{ description }}

A Fenwick tree answers to bits, not to scans: every value sits under a
cell, the lowest set bit picks the step an add climbs and a prefix walks
back down, and no walk ever touches more cells than the bit-length of
the size. Every prefix is checked against the running list-sum reference
after every op, and the one-pass fold rebuilds cells identical to one
add per value.

## Why

A plain list answers a prefix sum by walking every element below the
count. The tree keeps a cell per index whose window is the lowest-bit
run ending there, so a query reads at most `bit_length(n)` cells and an
add rewrites the same few. This tool exists to *show* that, not to
assert it:

```sh
$ {{ npm_name }} sum --values fixtures/values.txt 5
```

Every claim below is a comparison the demo computes at run time, and
`selftest` refuses to pass when one stops holding.

## The six rules

1. **Every prefix equals the running list-sum reference.** On seeded
   add/sum storms, `tree.prefix(k)` equals `sum(values[:k])` after
   every single op -- that equality is the whole product.
2. **No walk visits more cells than the bit-length of the size.** The
   cells a climb and a descent visit are counted, and the census proves
   the bound on a thousand cells.
3. **The one-pass fold equals one add per value.** Building the tree
   from an array in a single pass leaves cells identical to the tree
   built cell by cell, at every size including empty and lone.
4. **A range is two prefixes and the slice it names.** `range_sum`
   answers exactly `sum(values[low:high])`, or the window is refused.
5. **An add shifts the mirror and the cells together.** The value list
   beside the cells is the invariant's reference, never a fallback.
6. **The empty and lone trees answer honestly.** Empty prefixes are
   zero, a lone cell answers itself, and an index outside the tree is
   refused rather than folded.

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} demo
uv run {{ npm_name }} sum --values fixtures/values.txt 5
uv run {{ npm_name }} add 2 7
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `build [--values FILE] [--count N] [--seed S]` | load a tree and print the cells as they stand |
| `add [--values FILE] INDEX DELTA` | shift one value and show the climb the cells took |
| `sum [--values FILE] COUNT` | the prefix of this many values, walked down the bits |
| `range [--values FILE] LOW HIGH` | the window between two indices, two prefixes deep |
| `demo` | six stories about cells and bits, with real numbers |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

`fixtures/values.txt` is one integer value per line; blank lines and
lines starting with `#` are skipped. Without `--values` the tree is
built from the seeded generator instead. Indices handed to the tree are
**zero-based**; the cells underneath are one-based, and the module
docs carry the difference. Any index or count outside the tree is
refused with exit 2, never wrapped around.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the invariants hold |
| 1 | the tree stayed dishonest after the ops (never on a healthy run) |
| 2 | the input cannot be read: a bad file, a bad index, a bad count |

## Files

```
src/{{ package_name }}/fenwick.py    the cells, the walks, the invariants
src/{{ package_name }}/values.py     the whole numbers a tree accepts
src/{{ package_name }}/streams.py    corpora in, snapshots out
src/{{ package_name }}/workload.py   seeded storms and walk censuses, re-checked
src/{{ package_name }}/demo.py       six stories, every claim computed
src/{{ package_name }}/cli.py        the command line
src/{{ package_name }}/selftest.py   the invariants, runnable in a checkout
fixtures/values.txt                  a corpus the smoke test builds on
smoke.sh                             the tool driven the way a user drives it
```

## Non-goals

No floats, no duplicate-index policy beyond a plain list mirror, no
persisted storage, no concurrent writers, no suffix or sliding-window
queries. The bit-length bound belongs to the walks shown here; a tree
that grows and shrinks under your feet needs the rebuild, which the
fold provides and the selftest checks. This is a tool for showing what
the lowest bit buys a sum, not a replacement for `itertools.accumulate`.
