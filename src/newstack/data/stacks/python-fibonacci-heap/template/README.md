# {{ title }}

{{ description }}

A Fibonacci heap ranks integer-keyed items so pop-min replays the
plain `sorted(keys)`, decrease-key drops a tracked item and a
cascading cut pays the marked-children debt — the move ordinary
heaps lack. Every degree stays under the documented log bound, and
every figure is re-checked from raw links, never trusted.

## Why

A heap earns trust the only way a structure can: its answers must
equal a dumb sort's, on every workload, for every question. So this
tool exists to *show* that, not to state it:

```sh
$ {{ npm_name }} size --items fixtures/items.txt
```

Every claim below is a comparison the selftest computes at run time
against the real modules, and `selftest` refuses to pass when one
stops holding. The falsifiable core is the drain: `brute.py` sorts
with no structure at all and reads the forest through raw links, and
every pop sequence, degree, and answer the heap returns must be the
identical answer.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the pop sequence is the plain sort | a heap out of order | `pop == sorted(corpus)` on every seeded mixed stream |
| every degree stays under the bound | a forest that outgrows log n | the degree walk recomputes from raw links after every move |
| decrease-key keeps heap order | a cut that flips a parent | the audit walk runs on every decreased forest |
| a cascading cut pays the debt | an unpaid marked child | the storm audits after every decrease, never at the end |
| decrease-key targets are tracked by handle | a blind key hunt | `push` hands back the `Handle` every `decrease` needs |
| empty and single answer quietly | a crash at the edges | peek, pop, and size on zero and one item |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} peek --items fixtures/items.txt
uv run {{ npm_name }} decrease --items fixtures/items.txt 2 -4000
uv run {{ npm_name }} size --items fixtures/items.txt
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `push --items FILE KEY` | the heap with one more item, and its handle |
| `pop --items FILE` | the smallest key, released |
| `decrease --items FILE ITEM KEY` | the heap after a tracked drop |
| `peek --items FILE` | the next release, without releasing it |
| `size --items FILE` | live items and the live keys |
| `demo` | six stories about the forest, with real numbers |
| `selftest` | the invariants, runnable in a fresh checkout |

Decrease-key has no key-based lookup: the forest tracks items, and
`push` hands back the `Handle` a later decrease needs. The CLI maps
the 1-based item number of the list position onto that handle.

## Input format

`fixtures/items.txt` is one signed 32-bit integer per line, the key
the heap ranks by. Blank lines and lines starting with `#` are
skipped; every other line must be an integer — floats, words, and
oversized values are refused by name.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the invariants hold |
| 1 | the heap is empty, a story fails |
| 2 | the input cannot be read: a bad file, an increase sold as a decrease, a stale handle |

## Files

```
src/{{ package_name }}/heap.py       the forest, the cuts, the questions
src/{{ package_name }}/keys.py       the gate the integers pass
src/{{ package_name }}/brute.py      the sort and walk that are the oracle
src/{{ package_name }}/corpus.py     item lists in, snapshots out
src/{{ package_name }}/workload.py   seeded storms, audited per move
src/{{ package_name }}/demo.py       six stories, every claim computed
src/{{ package_name }}/cli.py        the command line
src/{{ package_name }}/selftest.py   the invariants, runnable in a checkout
fixtures/items.txt                   a corpus the smoke test builds on
smoke.sh                             the tool driven the way a user drives it
```

## Non-goals

No floats, no strings-as-keys, no keys past the signed 32-bit range,
no delete-arbitrary, no meld, no persisted storage, no concurrent
mutators, no generic values hung on the nodes. The forest is the
honest linked Fibonacci heap it is: a tool for showing what lazy
consolidation buys a drain, not a replacement for `sorted()`.
