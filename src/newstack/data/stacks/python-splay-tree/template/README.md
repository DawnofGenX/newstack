# {{ title }}

{{ description }}

A splay tree seats integer keys so the in-order walk is always the
plain `sorted(keys)`, and every access — insert, lookup, min, max —
rides the touched node to the root. The ride is three moves: zig,
zig-zig, zig-zag. The promise is checked, never assumed: after a hit
the key sits nowhere else but the root, and the walk cannot tell a
splay from stillness.

## Why

A tree earns trust the only way a structure can: its answers must
equal a dumb sort's, on every workload, for every question — and its
promise must hold after every move. So this tool exists to *show*
that, not to state it:

```sh
$ {{ npm_name }} has --keys fixtures/keys.txt 42
```

Every claim below is a comparison the selftest computes at run time
against the real modules, and `selftest` refuses to pass when one
stops holding. The falsifiable core is the walk and the root:
`brute.py` sorts with no structure at all and reads the root from
raw links, and every order, every ride, and every link the tree
returns must be the identical answer.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the walk is the plain sort | a tree out of order | `flatten() == sorted(live)` on every seeded mixed workload |
| the touch rides to the root | a lookup that forgot to splay | the root question after every access, in the storm and the tangle |
| a splay preserves the walk | a rotation that loses a key | `flatten()` equal before and after every splay |
| min and max ride up on request | a request answered in place | `minimum()` / `maximum()` leave the key at the root |
| an absent remove is refused | a silent half-delete | `TreeError` names the key, the tree is untouched |
| a double insert is quiet | a key seated twice | size and walk unchanged; the seated node still rides |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} iter --keys fixtures/keys.txt
uv run {{ npm_name }} has --keys fixtures/keys.txt 42
uv run {{ npm_name }} max --keys fixtures/keys.txt
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `add --keys FILE KEY` | the tree with one more key seated, rider at the root |
| `remove --keys FILE KEY` | the tree with one key unseated |
| `has --keys FILE KEY` | whether a key is seated, touched to the root |
| `iter --keys FILE` | the in-order walk, the sort itself |
| `min --keys FILE` | the smallest key, ridden to the root |
| `max --keys FILE` | the largest key, ridden to the root |
| `demo` | six stories about touches, with real numbers |
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
src/{{ package_name }}/tree.py       the tree, the splays, the questions
src/{{ package_name }}/keys.py       the gate the integers pass
src/{{ package_name }}/brute.py      the sort and the root that are the oracle
src/{{ package_name }}/corpus.py     key lists in, snapshots out
src/{{ package_name }}/workload.py   seeded storms, the promise kept per move
src/{{ package_name }}/demo.py       six stories, every claim computed
src/{{ package_name }}/cli.py        the command line
src/{{ package_name }}/selftest.py   the invariants, runnable in a checkout
fixtures/keys.txt                    a corpus the smoke test builds on
smoke.sh                             the tool driven the way a user drives it
```

## Non-goals

No floats, no strings-as-keys, no keys past the signed 32-bit range,
no persisted storage, no concurrent mutators, no generic values hung
on the nodes, no amortized-cost accounting. The tree is the honest
parent-linked splay it is: a tool for showing what self-adjustment
promises a walk, not a replacement for `sorted()`.
