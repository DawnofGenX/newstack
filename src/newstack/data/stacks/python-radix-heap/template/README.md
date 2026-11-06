# {{ title }}

{{ description }}

A radix heap answers to bits, not to comparisons: every integer key sits
in a bucket chosen by how far its bits run from the base the window
stands on, and pop-min reads the buckets in order instead of asking
which of two keys is smaller. A monotone stream -- every push at or
above the last pop -- walks the window forward and spends no full
rebuild at all; a backwards push is answered honestly with exactly one.

## Why

A comparison heap spends its edits asking which key is smaller and
carries the answer up the tree. The radix heap never asks: bucket order
*is* key order inside the window, so a pop reads lists in order and the
answer is arithmetic. This tool exists to *show* that, not to assert it:

```sh
$ {{ npm_name }} pop --keys fixtures/keys.txt 5
```

Every claim below is a comparison the demo computes at run time, and
`selftest` refuses to pass when one stops holding.

## The six rules

1. **Pop-min drains the sorted corpus.** On seeded mixed streams, the
   pop sequence equals `sorted(corpus)` exactly -- no comparison was
   ever made to get there.
2. **Every key sits at its bit-length-from-base bucket.** After every
   push, every pop, every rebuild: `bucket_of(key, base)` is where the
   key actually waits.
3. **A monotone stream never pays a rebuild.** 96 ascending pushes,
   checked after each; the window only walks forward.
4. **A mixed storm keeps the invariant after every op.** 160 seeded
   pushes and pop-mins, the invariant re-read after each one.
5. **A backwards push buys exactly one rebuild.** The fallback for a
   non-monotone stream resets the window; the answer survives.
6. **The window never drops a survivor behind.** After pops the base
   sits under every held key, and a rebuild re-files everything.

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} demo
uv run {{ npm_name }} pop --keys fixtures/keys.txt 5
uv run {{ npm_name }} push 30
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `build [--keys FILE] [--count N] [--seed S]` | load a heap and print where the keys sit |
| `pop [--keys FILE] [ROUNDS]` | the next pops, in the order the buckets read |
| `push [--keys FILE] KEYS...` | drop keys in their buckets, report the seat |
| `demo` | six stories about buckets and bits, with real numbers |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

`fixtures/keys.txt` is `key value` per line, whole numbers from zero
up. Blank lines and lines starting with `#` are skipped. Without
`--keys` the heap is built from the seeded generator instead. Keys
below zero or wider than 65 bits have no bucket and are refused.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the invariants hold |
| 1 | the heap drained before the rounds ran out |
| 2 | the input cannot be read: a bad file, a bad key, a bad seed |

## Files

```
src/{{ package_name }}/heap.py       the buckets, the window, the invariants
src/{{ package_name }}/keys.py       the whole numbers a window accepts
src/{{ package_name }}/streams.py    corpora in, snapshots out
src/{{ package_name }}/workload.py   mixed and monotone storms, re-checked
src/{{ package_name }}/demo.py       six stories, every claim computed
src/{{ package_name }}/cli.py        the command line
src/{{ package_name }}/selftest.py   the invariants, runnable in a checkout
fixtures/keys.txt                    a stream the smoke test builds on
smoke.sh                             the tool driven the way a user drives it
```

## Non-goals

No negative keys, no floating-point keys, no duplicate-key policy, no
persisted storage, no concurrent writers. The amortized-constant claim
belongs to monotone streams; a mixed stream pays rebuilds and stays
correct. This is a tool for showing what bits buy a queue, not a
replacement for `heapq`.
