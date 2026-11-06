# {{ title }}

{{ description }}

A Burkhard-Keller tree keeps words one edge per distance apart: the child at
edge `d` holds the words exactly `d` edits from the node above it. To answer
"every word within 2 of `helo`" the walk measures once per node and steps only
into children whose edge lies in `[gap - 2, gap + 2]` — because edit distance
obeys the triangle inequality, a node outside that window cannot hold an
answer, and it is skipped without being opened.

## Why

A full scan measures the query against every word, which is honest and slow.
The tree gives the same answers after measuring a fraction of the corpus —
and this tool exists to *show* that, not to assert it:

```
$ {{ npm_name }} search --words fixtures/words.txt --word helo --distance 2
```

Every claim below is a comparison the demo computes at run time, and
`selftest` refuses to pass when one stops holding.

## The six rules

1. **The distance counts edits.** Insertions, deletions, substitutions.
   Symmetric, zero only between equal words.
2. **A limit stops the walk early.** Past the limit the answer is
   `limit + 1`, which says "no" without computing "how much no".
3. **The tree looks at a fraction of the corpus.** One walk, same words as
   the scan, a fortieth of the measurements on the demo corpus.
4. **Insertion order changes the shape, never the answers.** Two trees,
   same words, different depth, identical hits.
5. **Transpositions are not a metric.** Optimal string alignment breaks the
   triangle inequality, so the tree scans instead of pruning — and says so.
6. **A repeat is not a second node.** A word enters once; asking again costs
   one comparison and no memory.

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} demo
uv run {{ npm_name }} distance kitten sitting
uv run {{ npm_name }} search --words fixtures/words.txt --word helo --distance 2
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `distance LEFT RIGHT [--limit N]` | the edits between two strings, plain and with transpositions |
| `search --words FILE --word W [--distance N] [--json] [--transpositions]` | every word within N, pruned or scanned |
| `nearest --words FILE --word W` | the closest words, however far |
| `tree --words FILE` | the shape of the tree and one walk through it |
| `demo` | six stories about searching by distance, with real numbers |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

`fixtures/words.txt` is one word per line. Blank lines and lines starting
with `#` are skipped. Case is kept unless `--lowercase` is passed.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was found, or the invariants hold |
| 1 | nothing was within the distance |
| 2 | the input cannot be read: a bad file, a bad limit, a bad word |

## Files

```
src/{{ package_name }}/distance.py    edit distance, its limit, and the metric claim
src/{{ package_name }}/tree.py        the tree, the pruned walk, the honest scan
src/{{ package_name }}/corpus.py      word lists and a deterministic generator
src/{{ package_name }}/demo.py        six stories, every claim computed
src/{{ package_name }}/cli.py         the command line
src/{{ package_name }}/selftest.py    the invariants, runnable in a fresh checkout
fixtures/words.txt                    a corpus the smoke test walks
smoke.sh                              the tool driven the way a user drives it
```

## Non-goals

No deletion-heavy distances, no weighted edits, no persistent storage, no
approximate answers for speed. This is a tool for showing where pruning is
allowed and where it is a lie, not a replacement for a search index.
