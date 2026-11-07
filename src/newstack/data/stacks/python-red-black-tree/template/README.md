# {{ title }}

{{ description }}

A red-black tree stores keys as a shape: the root stands black, no red
node fathers a red child, and every root-to-leaf path counts the same
black height. The in-order walk is the sorted list of the keys held;
the checker in `check.py` walks the tree after every operation and
names every broken promise by name.

## Why

A tree earns trust the only way a stored structure can: its walk must
equal `sorted` of the live keys, and its shape must answer the
checker, after every single insert and removal. So this tool exists to
*show* that, not to state it:

```sh
$ {{ npm_name }} iter --keys fixtures/keys.txt
```

Every claim below is a comparison the selftest computes at run time
against the real modules, and `selftest` refuses to pass when one stops
holding. The falsifiable core is the storm: `workload.py` drives mixed
seeded sequences and re-checks the walk, the count, and the checker
after every op — a break counter that cannot move off zero.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the walk is the sorted list | a walk that misses or invents a key | every seeded storm, after every op |
| the checker names nothing | a red root, a red father, a height split | the shipped checker, tested itself |
| black heights agree at the edges | a tree gone jagged under deletion | the edge comparison in the selftest |
| a removal keeps the walk sorted | a fixup that drops or duplicates a key | the removals section and the tests |
| remove of an absent key refuses | a silent no-op on a key never held | the refuses checks and the CLI exit |
| a rebuild answers identically | insertion order leaking into an answer | trees built in opposite orders |
| the gate keeps junk out | a float, a bool, a key past the edge | the gate section |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} iter --keys fixtures/keys.txt
uv run {{ npm_name }} has --keys fixtures/keys.txt 4
uv run {{ npm_name }} remove --keys fixtures/keys.txt 4
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `add --keys FILE K...` | store keys, report what the tree holds after |
| `remove --keys FILE K...` | drop held keys; refuse an absent one by name |
| `has --keys FILE K...` | membership, exactly |
| `iter --keys FILE` | the in-order walk, ascending |
| `selftest` | the invariants, runnable in a fresh checkout |
| `demo` | six stories about colours and walks, with real numbers |

## Input format

`fixtures/keys.txt` is one bounded integer per line. Blank lines and
lines starting with `#` are skipped. Keys past 10^9 are refused by
name, never quietly stored.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the invariants hold |
| 1 | the key is not held, the walk is empty |
| 2 | the input cannot be read: a bad file, a half key, an absent removal |

## Files

```
src/{{ package_name }}/keys.py       the gate the keys pass
src/{{ package_name }}/check.py      the checker that names broken shapes
src/{{ package_name }}/node.py       immutable nodes and the fixup
src/{{ package_name }}/tree.py       the black-rooted tree and its audit
src/{{ package_name }}/corpus.py     key lists in, snapshots out
src/{{ package_name }}/workload.py   seeded storms, re-checked per op
src/{{ package_name }}/demo.py       six stories, every claim computed
src/{{ package_name }}/cli.py        the command line
src/{{ package_name }}/selftest.py   the invariants, runnable in a checkout
fixtures/keys.txt                    a corpus the smoke test builds on
smoke.sh                             the tool driven the way a user drives it
```

## Non-goals

No floats, no half keys, no keys past the edge, no duplicates ("a key
is stored once"), no persisted storage, no concurrent writers, no
values attached to keys, no generic payloads. The tree is the honest
colour-and-rotation structure it is: a tool for showing what the
invariants cost and buy, not a replacement for `sorted`.
