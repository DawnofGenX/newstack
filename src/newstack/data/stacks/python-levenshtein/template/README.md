# {{ title }}

{{ description }}

Unit-cost edit distance counts the fewest changes — insert a letter,
delete a letter, substitute a letter, one change each — that turn one
lowercase string into another. The row walk answers; the bare
recursion proves; and a nearest answer must equal the brute-force
scan's argmin with ties handed to the lexicographically first entry.

## Why

A distance earns trust the only way a count can: it must equal a
dumber computation's, on every pair, from both sides, and never beat a
detour. So this tool exists to *show* that, not to state it:

```sh
$ {{ npm_name }} distance knight light
```

Every claim below is a comparison the selftest computes at run time
against the real modules, and `selftest` refuses to pass when one stops
holding. The falsifiable core is the oracle: `oracle.py` recomputes
every branch from scratch, memo-free, capped at eight letters per side,
and every distance the row walk returns must be the identical integer.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the walk equals the bare recursion | a row walk out of step with the oracle | every shipped pair under the cap, both in the selftest and the tests |
| a distance is symmetric | a direction the count forgot | every shipped pair and every seeded triple |
| a detour never beats the direct change | a triangle the distance broke | the shipped triples and seeded triples |
| to nothing is a change per letter | an edge case off by one | `distance(a, "")` against `len(a)` |
| nearest is the scan's argmin, ties first by letters | an argmin out of the documented order | the scan comparison on every query |
| the gate keeps strangers out of the matrix | uppercase, digits, lists | the word gate section |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} distance cat cart
uv run {{ npm_name }} nearest --words fixtures/words.txt crt
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `distance LEFT RIGHT [--json]` | the fewest unit changes between two strings |
| `nearest --words FILE QUERY [--json]` | the corpus entry with the smallest distance |
| `demo` | six stories about letters and changes, with real numbers |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

`fixtures/words.txt` is one lowercase word per line, letters `a`-`z`
only, one to sixty-four of them. Blank lines and lines starting with
`#` are skipped. `distance` also admits the empty string as a side —
it names no word, yet the distance to it is exactly a change per
letter. A nearest tie goes to the lexically first entry, documented
and enforced.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the invariants hold |
| 1 | the nearest entry is not an exact match, the invariants broke |
| 2 | the input cannot be read: a bad file, a bad word, a bad seed |

## Files

```
src/{{ package_name }}/distance.py    the row walk, the scan, the tie rule
src/{{ package_name }}/oracle.py      the bare recursion, short words only
src/{{ package_name }}/words.py       the gate the letters pass
src/{{ package_name }}/corpus.py      word lists in, snapshots out
src/{{ package_name }}/workload.py    seeded storms, re-checked per draw
src/{{ package_name }}/demo.py        six stories, every claim computed
src/{{ package_name }}/cli.py         the command line
src/{{ package_name }}/selftest.py    the invariants, runnable in a checkout
fixtures/words.txt                    a corpus the smoke test builds on
smoke.sh                              the tool driven the way a user drives it
```

## Non-goals

No uppercase, no digits, no punctuation, no string past sixty-four
letters, no transpositions for free, no weighted changes, no persisted
storage, no memoized oracle. The recursion is exponential on purpose:
past eight letters per side it refuses rather than runs, and the row
walk carries everything longer.
