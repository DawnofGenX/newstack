# {{ title }}

{{ description }}

A van Emde Boas tree seats integers in the fixed universe
`[0, 256)` — eight bits, four levels deep — so successor, predecessor,
membership, min, and max come back through cluster arithmetic. The
falsifiable core is a scan: `brute.py` walks a sorted list with no
structure at all, and every seek the tree answers must equal the
scan's, on every seeded storm, after every move.

## Why

A structure earns trust the only way a structure can: its answers
must equal a dumb scan's, on every workload, for every question. So
this tool exists to *show* that, not to state it:

```sh
$ {{ npm_name }} succ --keys fixtures/keys.txt 100
```

Every claim below is a comparison the selftest computes at run time
against the real modules, and `selftest` refuses to pass when one
stops holding. The universe is small and fixed on purpose — a
two-hundred-fifty-six-seat table the whole structure can be audited
against, honestly, in a storm.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| successor is the scan | a seek that skips a seat | `successor(q) == scan_successor(live, q)` on every seeded storm step |
| predecessor is the scan | a seek that overshot | `predecessor(q) == scan_predecessor(live, q)` on every storm step |
| membership is set membership | a phantom or lost seat | `member(q) == (q in live)` after every insert and remove |
| the walk is the plain sort | a tree out of order | `live() == sorted(live)` on every workload |
| an empty tree answers None | a invented answer | min, max, succ, pred on the empty tree all `None` |
| an absent remove is refused | a silent half-delete | `TreeError` names the key, the tree is untouched |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} succ --keys fixtures/keys.txt 100
uv run {{ npm_name }} has --keys fixtures/keys.txt 42
uv run {{ npm_name }} min --keys fixtures/keys.txt
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `add --keys FILE KEY` | the tree with one more seat |
| `remove --keys FILE KEY` | the tree with one seat unseated |
| `has --keys FILE KEY` | whether a key is seated |
| `succ --keys FILE KEY` | the smallest seat >= KEY |
| `pred --keys FILE KEY` | the largest seat <= KEY |
| `min --keys FILE` / `max --keys FILE` | the ends of the tree |
| `demo` | six stories about seats, with real numbers |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

`fixtures/keys.txt` is one integer of `[0, 256)` per line. Blank
lines and lines starting with `#` are skipped; every other line must
be a seat — floats, words, negatives, and values past 255 are refused
by name.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the invariants hold |
| 1 | the key is not seated, the seek came back None, a story fails |
| 2 | the input cannot be read: a bad file, a bad key, an absent remove |

## Files

```
src/{{ package_name }}/tree.py       the tree, the clusters, the questions
src/{{ package_name }}/keys.py       the gate the seats pass
src/{{ package_name }}/brute.py      the scans that are the oracle
src/{{ package_name }}/corpus.py     key lists in, snapshots out
src/{{ package_name }}/workload.py   seeded storms, re-checked per move
src/{{ package_name }}/demo.py       six stories, every claim computed
src/{{ package_name }}/cli.py        the command line
src/{{ package_name }}/selftest.py   the invariants, runnable in a checkout
fixtures/keys.txt                    a corpus the smoke test builds on
smoke.sh                             the tool driven the way a user drives it
```

## Non-goals

No keys outside `[0, 256)`, no wider universe, no floats, no
strings-as-keys, no persisted storage, no concurrent mutators. The
tree is the honest fixed-universe vEB it is: a tool for showing what
cluster arithmetic owes a scan, not a general integer dictionary.
