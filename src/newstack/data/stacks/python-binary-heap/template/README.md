# {{ title }}

{{ description }}

A min-heap seats integer keys in a plain list, sifted by hand:
sift-up walks a fresh key to its resting slot, sift-down hands each
slot to its smaller child. No `heapq`, no cleverness. The promise is
checked, never assumed: the drain order of any push/pop storm must
spell the plain `sorted(pushed)`, and the shipped checker walks the
array for the parent rule after every operation.

## Why

A heap earns trust the only way a structure can: its answers must
equal a dumb sort's, on every storm, for every question — and its
shape must hold after every move. So this tool exists to *show*
that, not to state it:

```sh
$ {{ npm_name }} peek --keys fixtures/keys.txt
```

Every claim below is a comparison the selftest computes at run time
against the real modules, and `selftest` refuses to pass when one
stops holding. The falsifiable core is the drain and the shape:
`oracle.py` sorts with no structure at all and walks the array slot
by slot, and every answer the heap returns must be the identical
answer.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the drain is the plain sort | a heap out of order | `drain() == sorted(pushed)` on every seeded storm |
| the parent rides no higher | an array out of shape | the shipped checker walks the array after every op |
| the head is the minimum | a peek that lied | the head against `min(live)` after every move |
| an empty pop is refused | a silent zero | `HeapError` names the emptiness, the heap is untouched |
| repeats keep every seat | a key swallowed twice | one per seat, `len` and the drain agree |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} len --keys fixtures/keys.txt
uv run {{ npm_name }} peek --keys fixtures/keys.txt
uv run {{ npm_name }} push --keys fixtures/keys.txt 42
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `push --keys FILE KEY` | the heap with one more key seated |
| `pop --keys FILE` | the smallest key handed over, the heap reshaped |
| `peek --keys FILE` | the smallest key, in place |
| `len --keys FILE` | how many keys are seated |
| `demo` | six stories about sifts, with real numbers |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

`fixtures/keys.txt` is one signed 32-bit integer per line. Blank
lines and lines starting with `#` are skipped; every other line must
be an integer — floats, words, and oversized values are refused by
name. Repeats are welcome: a heap is a multiset.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the invariants hold |
| 1 | the heap is empty, a story fails |
| 2 | the input cannot be read: a bad file, a bad key |

## Files

```
src/{{ package_name }}/heap.py        the heap, the sifts, the questions
src/{{ package_name }}/keys.py        the gate the integers pass
src/{{ package_name }}/oracle.py      the sort and the checker that are the oracle
src/{{ package_name }}/corpus.py      key lists in, snapshots out
src/{{ package_name }}/workload.py    seeded storms, the promise kept per move
src/{{ package_name }}/demo.py        six stories, every claim computed
src/{{ package_name }}/cli.py         the command line
src/{{ package_name }}/selftest.py    the invariants, runnable in a checkout
fixtures/keys.txt                     a corpus the smoke test builds on
smoke.sh                              the tool driven the way a user drives it
```

## Non-goals

No floats, no strings-as-keys, no keys past the signed 32-bit range,
no decrease-key, no persisted storage, no concurrent mutators, no
generic values hung on the slots, no heapq. The heap is the honest
array it is: a tool for showing what a sift promises a drain, not a
replacement for `sorted()`.
