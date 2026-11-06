# {{ title }}

{{ description }}

A skip list keeps its towers short with coin flips instead of rotations:
every node stores a key, a value, and one forward link per story it
stands on, and every link carries the width — the slots at the bottom
lane it spans. `rank` sums the widths it skips, `select` walks widths
down to a position, and the two are exact inverses without ever sorting.

## Why

A balanced tree rotates to stay shallow and spends edits telling its
parents about it. The skip list flips a coin per insert and gets the
same `O(log n)` with links a caller can walk. This tool exists to *show*
that, not to assert it:

```sh
$ {{ npm_name }} rank --pairs fixtures/pairs.txt 30
```

Every claim below is a comparison the demo computes at run time, and
`selftest` refuses to pass when one stops holding.

## The six rules

1. **Rank answers what bisect answers.** Key by key, against a plain
   sorted list, before and after 15 deletions.
2. **Select and rank are exact inverses.** Position to key back to
   position, every position in the map.
3. **Same seed, same tower, byte for byte.** Two maps from one seed, and
   a replay from stored pairs, leave identical level counts.
4. **A different seed shuffles the shape, never the order.** Same pairs,
   two shapes; the sorted answer is the same map.
5. **A delete repairs every width it broke.** Knock down a third of the
   towers and rank still answers what bisect answers.
6. **The towers stay as short as log2 promises.** Tallest tower within
   a few stories of `log2(size)`, level counts falling as levels climb.

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} demo
uv run {{ npm_name }} rank --pairs fixtures/pairs.txt 30
uv run {{ npm_name }} select --count 64 3
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `build [--pairs FILE] [--count N] [--seed S]` | load a map and print the ladder the coins left |
| `rank [--pairs FILE] KEYS...` | how many stored keys sit below each key |
| `select [--pairs FILE] POSITIONS...` | the pair sitting at each position |
| `demo` | six stories about coins and order, with real numbers |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

`fixtures/pairs.txt` is `key value` per line, integers only. Blank lines
and lines starting with `#` are skipped. Without `--pairs` the map is
built from the seeded generator instead.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the invariants hold |
| 1 | a position held nothing |
| 2 | the input cannot be read: a bad file, a bad seed, a key outside the order |

## Files

```
src/{{ package_name }}/keys.py      the keys accepted and the order they share
src/{{ package_name }}/coins.py     the seeded flips that decide tower heights
src/{{ package_name }}/map.py       the map: links, widths, rank, select
src/{{ package_name }}/stack.py     pair streams in, snapshots out
src/{{ package_name }}/demo.py      six stories, every claim computed
src/{{ package_name }}/cli.py       the command line
src/{{ package_name }}/selftest.py  the invariants, runnable in a fresh checkout
fixtures/pairs.txt                  a stream the smoke test builds from
smoke.sh                            the tool driven the way a user drives it
```

## Non-goals

No duplicate keys, no persisted storage, no concurrent writers, no
`p != 1/2` ladders. This is a tool for showing what coin flips buy an
ordered map, not a replacement for a database index.
