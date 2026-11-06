# {{ title }}

{{ description }}

A treap answers to two orders at once: keys fall through it the way a
search tree orders them, and a seeded draw decides who stands above
whom, so every parent's number sits at or below its children's. insert,
delete, and split are all one expression, `merge` — the tree is never
repaired after an edit, it is re-formed from halves that already hold.

## Why

A balanced tree rotates to stay shallow and spends edits telling its
parents about it. The treap draws a number per insert and gets the same
`O(log n)` depth with no rotations at all — and because the draws come
from one seed, the shape is arithmetic: same seed, same pairs, identical
tree. This tool exists to *show* that, not to assert it:

```sh
$ {{ npm_name }} rank --keys fixtures/keys.txt 30
```

Every claim below is a comparison the demo computes at run time, and
`selftest` refuses to pass when one stops holding.

## The six rules

1. **Rank answers what bisect answers.** Key by key, against a plain
   sorted list, probes before and after a mixed storm.
2. **Select and rank are exact inverses.** Position to key back to
   position, every position in the tree.
3. **A mixed workload never breaks either order.** 160 seeded inserts,
   deletes, probes, and ranks; both orders re-counted after every op.
4. **A split loses nothing the join returns.** Halves hold their sides,
   the join restores the keys and the exact shape.
5. **The seed owns the shape.** Same seed leaves the same walk, a
   rebuild from (key, priority) replays it, another seed shuffles the
   shape but never the order.
6. **The tree stays as deep as the draws promise.** Depth near
   `bit_length + 1`, and neither order broken anywhere.

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
| `build [--keys FILE] [--count N] [--seed S]` | load a tree and print the shape the draws left |
| `rank [--keys FILE] KEYS...` | how many stored keys sit below each key |
| `select [--keys FILE] POSITIONS...` | the pair sitting at each position |
| `split [--keys FILE] PIVOT` | cut at a pivot, merge the halves, report the leak |
| `demo` | six stories about heaps and order, with real numbers |
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
| 2 | the input cannot be read: a bad file, a bad seed, a key outside the order |

## Files

```
src/{{ package_name }}/draws.py      the seeded stream deciding the heap
src/{{ package_name }}/keys.py       the keys accepted and the order they share
src/{{ package_name }}/treap.py      split, merge, rank, select
src/{{ package_name }}/workload.py   a mixed storm re-checking both orders
src/{{ package_name }}/streams.py    pair streams in, snapshots out
src/{{ package_name }}/demo.py       six stories, every claim computed
src/{{ package_name }}/cli.py        the command line
src/{{ package_name }}/selftest.py   the invariants, runnable in a checkout
fixtures/keys.txt                    a stream the smoke test builds on
smoke.sh                             the tool driven the way a user drives it
```

## Non-goals

No duplicate keys, no persisted storage, no concurrent writers, no
balanced-by-rotations promises. This is a tool for showing what one
seeded draw buys an ordered tree, not a replacement for a database
index.
