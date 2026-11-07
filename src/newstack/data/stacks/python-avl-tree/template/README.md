# {{ title }}

{{ description }}

An AVL tree seats integer keys so the in-order walk is always the
plain `sorted(keys)`, and every balance factor stays inside `-1, 0, 1`
after every insert and every remove — a rotation hands the height
over, never loses it. The tree reaches balance by rotations; every
figure it stores is re-checked from raw structure, never trusted.

## Why

A tree earns trust the only way a structure can: its answers must
equal a dumb sort's, on every workload, for every question. So this
tool exists to *show* that, not to state it:

```sh
$ {{ npm_name }} iter --keys fixtures/keys.txt
```

Every claim below is a comparison the selftest computes at run time
against the real modules, and `selftest` refuses to pass when one
stops holding. The falsifiable core is the walk: `brute.py` sorts with
no structure at all and recomputes every factor from raw heights, and
every order, factor, and height the tree returns must be the identical
answer.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the walk is the plain sort | a tree out of order | `flatten() == sorted(live)` on every seeded mixed workload |
| every factor sits in -1, 0, 1 | a stale height or a flipped rotation | the factor walk recomputes from raw structure after every move |
| a rotation preserves the walk | a rebuild that loses a key | `flatten()` equal before and after `rebuild()`, audit clean |
| the height stays under the ceiling | a tree that outgrows AVL | `height <= ceil(1.44 * log2(n + 2))` on every storm |
| an absent remove is refused | a silent half-delete | `TreeError` names the key, the tree is untouched |
| a double insert is quiet | a key seated twice | size and walk unchanged by the second insert |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} iter --keys fixtures/keys.txt
uv run {{ npm_name }} has --keys fixtures/keys.txt 42
uv run {{ npm_name }} height --keys fixtures/keys.txt
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `add --keys FILE KEY` | the tree with one more key seated |
| `remove --keys FILE KEY` | the tree with one key unseated |
| `has --keys FILE KEY` | whether a key is seated |
| `iter --keys FILE` | the in-order walk, the sort itself |
| `height --keys FILE` | the height, under the AVL ceiling |
| `demo` | six stories about balance, with real numbers |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

`fixtures/keys.txt` is one signed 32-bit integer per line. Blank
lines and lines starting with `#` are skipped; every other line must
be an integer — floats, words, and oversized values are refused by
name.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the invariants hold |
| 1 | the key is not seated, the tree is empty, a story fails |
| 2 | the input cannot be read: a bad file, a bad key, an absent remove |

## Files

```
src/{{ package_name }}/tree.py       the tree, the rotations, the questions
src/{{ package_name }}/keys.py       the gate the integers pass
src/{{ package_name }}/brute.py      the sort and walk that are the oracle
src/{{ package_name }}/corpus.py     key lists in, snapshots out
src/{{ package_name }}/workload.py   seeded storms, re-checked per move
src/{{ package_name }}/demo.py       six stories, every claim computed
src/{{ package_name }}/cli.py        the command line
src/{{ package_name }}/selftest.py   the invariants, runnable in a checkout
fixtures/keys.txt                    a corpus the smoke test builds on
smoke.sh                             the tool driven the way a user drives it
```

## Non-goals

No floats, no strings-as-keys, no keys past the signed 32-bit range,
no persisted storage, no concurrent mutators, no generic values hung
on the nodes. The tree is the honest singly-stored AVL it is: a tool
for showing what balance buys a walk, not a replacement for
`sorted()`.
