# {{ title }}

{{ description }}

A scapegoat tree answers to one rule: a child may hold under `alpha`
(0.7 by default) of its parent's live count. When a child tips past
it, no parent rotates — the tipped subtree is flattened to a sorted
run and rebuilt midpoint-first in one pass. Nothing is stored on a
node the walk cannot recompute, and every touch is counted, so the
ledger a workload leaves is arithmetic, not folklore.

## Why

A rotated tree stays shallow by spending edits on its parents. The
scapegoat tree stays shallow by rebuilding whole subtrees and paying
for them in one bill: a single insert can charge linear, while the
stream settles at `O(n log n)` — and this tool *shows* both numbers
rather than asserting them.

```sh
$ {{ npm_name }} build --count 64
```

Every claim below is a comparison the demo computes at run time, and
`selftest` refuses to pass when one stops holding.

## The six rules

1. **The rule is arithmetic.** A parent of ninety tolerates sixty-two
   through the ceiling and lands rebuilds on twenty-seven; alpha
   outside the open unit interval keeps no rule and is refused.
2. **The answers are bisect's.** Rank, select, and iteration against a
   plain sorted list, probes before and after a mixed storm.
3. **A rebuild is lossless.** Flattening returns the run the tree kept,
   key for key, and a midpoint rebuild holds the rule at every node.
4. **A storm never tips the rule.** 160 seeded inserts, deletes, and
   probes; the rule and the sorted run re-read after every op.
5. **The depth is the promise.** Depth stays under `log base 1/alpha of
   n, plus one` — counted on the tree, never assumed.
6. **The counter settles at n log n.** Ascending doubles pay under 3×,
   not the 4× a quadratic charge would bill; one insert still charges
   a real, sometimes linear, bill.

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} demo
uv run {{ npm_name }} rank --keys fixtures/keys.txt 30
uv run {{ npm_name }} select --count 64 3
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `build [--keys FILE] [--count N] [--alpha A]` | load a tree and print the ledger the rebuilds left |
| `rank [--keys FILE] [--alpha A] KEYS...` | how many stored keys sit below each key |
| `select [--keys FILE] [--alpha A] POSITIONS...` | the pair sitting at each position |
| `storm` | the seeded mixed storm and what it broke (hopefully nothing) |
| `demo` | six stories about rebuilds and order, with real numbers |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

`fixtures/keys.txt` is `key value` per line, integers only. Blank lines
and lines starting with `#` are skipped. Without `--keys` the tree is
built from the seeded generator instead.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the invariants hold |
| 1 | a position held nothing |
| 2 | the input cannot be read: a bad file, a bad alpha, a key outside the order |

## Files

```
src/{{ package_name }}/keys.py       the keys accepted and the order they share
src/{{ package_name }}/rules.py      alpha, the ceilings, the depth promise
src/{{ package_name }}/tree.py       rebuilds instead of rotations, counted
src/{{ package_name }}/streams.py    pair streams in, snapshots out
src/{{ package_name }}/demo.py       six stories, every claim computed
src/{{ package_name }}/cli.py        the command line
src/{{ package_name }}/selftest.py   the invariants, runnable in a checkout
fixtures/keys.txt                    a stream the smoke test builds on
smoke.sh                             the tool driven the way a user drives it
```

## Non-goals

No duplicate keys, no persisted storage, no concurrent writers, no
per-node sizes or parent links. This is a tool for showing what one
greedy rebuild rule buys an ordered tree, not a replacement for a
database index.
