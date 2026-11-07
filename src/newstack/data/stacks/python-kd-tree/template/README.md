# {{ title }}

{{ description }}

A kd-tree stores points as splits: at one level the plane divides on x,
at the next on y, and a point whose coordinate equals the split walks
right, never left. Membership walks the decisions; a rectangle answer
walks both sides whenever the box crosses a split; the nearest answer
is the brute-force argmin with the tie given to the smallest point.

## Why

A kd-tree earns trust the only way a query structure can: its answers
must equal a dumb scan's, on every corpus, after every insert. So this
tool exists to *show* that, not to state it:

```sh
$ {{ npm_name }} nearest --points fixtures/points.txt 9,9
```

Every claim below is a comparison the selftest computes at run time
against the real modules, and `selftest` refuses to pass when one stops
holding. The falsifiable core is the scan: `scan.py` walks the corpus
with one comparison per point, and every membership, rectangle, and
nearest answer the tree returns must be the identical answer, in the
identical order.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| membership is a set's answer | a `has` that misses or invents a point | every seeded corpus in the selftest and the tests |
| a rectangle answer is the filter | a `range` that stops at a split it crosses | the scan comparison on every corpus |
| the nearest answer is the argmin | a pruned subtree holding the true winner | the scan comparison, ties included |
| the tie goes to the smallest point | a `nearest` that answers a twin late | the equal-distance section |
| a rebuild from the walk answers identically | insertion order leaking into an answer | trees built in opposite orders |
| the gate keeps half-points out | a float, a bool, a point past the edge | the gate section |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} count --points fixtures/points.txt
uv run {{ npm_name }} has --points fixtures/points.txt 10,10
uv run {{ npm_name }} nearest --points fixtures/points.txt 9,9
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `add --points FILE X,Y...` | store points, report what the tree holds after |
| `has --points FILE X,Y...` | membership, exactly |
| `range --points FILE X1,Y1,X2,Y2` | every point in a box, in order |
| `nearest --points FILE X,Y` | the closest point, ties to the smallest |
| `count --points FILE` | size and whether the splits still divide |
| `demo` | six stories about splits and boxes, with real numbers |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

`fixtures/points.txt` is one `x,y` pair of bounded integers per line.
Blank lines and lines starting with `#` are skipped. Coordinates past
10^9 are refused by name, never quietly stored.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the invariants hold |
| 1 | the point is not held, the box holds nothing, the tree is empty |
| 2 | the input cannot be read: a bad file, a half-point, a bad seed |

## Files

```
src/{{ package_name }}/tree.py       the splits, the points, the audit
src/{{ package_name }}/points.py     the gate the pairs pass
src/{{ package_name }}/scan.py       the scan that is the oracle
src/{{ package_name }}/corpus.py     point lists in, snapshots out
src/{{ package_name }}/workload.py   seeded storms, re-checked per op
src/{{ package_name }}/demo.py       six stories, every claim computed
src/{{ package_name }}/cli.py        the command line
src/{{ package_name }}/selftest.py   the invariants, runnable in a checkout
fixtures/points.txt                  a corpus the smoke test builds on
smoke.sh                             the tool driven the way a user drives it
```

## Non-goals

No floats, no half-points, no points past the plane edge, no delete, no
duplicates beyond "a point is stored once", no persisted storage, no
concurrent writers, no third dimension. The tree is the honest
split-walk structure it is: a tool for showing what splits buy a point
set, not a replacement for `sorted`.
