# {{ title }}

{{ description }}

A binomial heap answers to shape, not to waiting: a tree of rank k
holds exactly 2^k keys, the forest stands one tree per rank, and the
ranks standing present are the bit pattern of the count. Meld unions
two forests by carrying links upward like binary addition -- the
answer a plain heap refuses, because a plain heap has no forest to
union.

## Why

A single tree bends under a second heap; melding means rebuilding.
The forest is already an addition: two forests become one by linking
equal ranks, every link a carry, and the smaller root of every link
stays on top. This tool exists to *show* that, not to assert it:

```sh
$ {{ npm_name }} meld 1 2 3
```

Every claim below is a comparison the demo computes at run time, and
`selftest` refuses to pass when one stops holding.

## The six rules

1. **Meld drains as the sorted concat.** On seeded heaps, meld then
   full drain equals `sorted(left + right)` exactly -- the pop-min of
   a union is the min of the union.
2. **A tree of rank k holds exactly 2^k keys.** Re-checked after
   every push, pop, and meld, all the way down the children.
3. **The forest holds one tree per rank.** After every op the ranks
   standing present equal the bit pattern of the count.
4. **A 160-op storm of pushes, pop-mins, and melds holds shape** --
   the invariant re-read after each op, the answers replayed against
   the seeded pool.
5. **Pop-min lifts a root and re-carries its orphans** -- the smaller
   root of every link stayed on top, and the count still adds up.
6. **An empty forest refuses** -- pop and peek on nothing raise,
   never answer zero.

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} demo
uv run {{ npm_name }} meld 1 2 3
uv run {{ npm_name }} pop --keys fixtures/keys.txt 5
uv run {{ npm_name }} size --keys fixtures/keys.txt
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `push [--keys FILE] KEYS...` | drop keys in, report the rank each reached |
| `pop [--keys FILE] [ROUNDS]` | the next pops, in the order the forest answers |
| `meld [--keys FILE] KEYS...` | union a heap with fresh keys -- the product |
| `size [--keys FILE] [--count N]` | the count, its bits, and the forest behind it |
| `peek [--keys FILE]` | the next pop, without paying for it |
| `demo` | six stories about forests and carries, with real numbers |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

`fixtures/keys.txt` is `key value` per line, whole numbers -- negatives
allowed, a forest orders by comparison, not by bits. Blank lines and
lines starting with `#` are skipped. Without `--keys` the heap is
built from the seeded generator instead.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the invariants hold |
| 1 | the forest drained before the rounds ran out |
| 2 | the input cannot be read: a bad file, a bad key, a bad seed |

## Files

```
src/{{ package_name }}/heap.py       the trees, the carries, the invariants
src/{{ package_name }}/keys.py       the whole numbers a forest accepts
src/{{ package_name }}/streams.py    corpora in, snapshots out
src/{{ package_name }}/workload.py   storms of pushes, pops, and melds
src/{{ package_name }}/demo.py       six stories, every claim computed
src/{{ package_name }}/cli.py        the command line
src/{{ package_name }}/selftest.py   the invariants, runnable in a checkout
fixtures/keys.txt                    a stream the smoke test builds on
smoke.sh                             the tool driven the way a user drives it
```

## Non-goals

No floating-point keys, no duplicate-key policy, no persisted storage,
no concurrent writers, no decrease-key. Meld is destructive: the donor
forest is emptied, never copied. This is a tool for showing what a
carrying forest buys a queue, not a replacement for `heapq`.
