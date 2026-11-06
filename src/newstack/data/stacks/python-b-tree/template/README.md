# {{ title }}

{{ description }}

A B-tree of order `t` keeps every node between `t - 1` and `2t - 1` keys: a
full node splits down the middle on the way down, and a short child is
refilled from a sibling across the separator before anything merges. Because
the fix happens during descent, not after, no node is ever overfull when a
key lands in it and no merge can starve a sibling — the tree shrinks from the
top and never goes jagged. The in-order walk is the sorted corpus whatever
got the tree there.

## Why

A balanced tree earns its balance by what refuses to break under a long
insert AND delete history, not by asserting it in a comment. So this tool
exists to *show* that, not to state it:

```
$ {{ npm_name }} load --keys fixtures/keys.txt --order 2
```

Every claim below is a comparison the selftest computes at run time against
the real modules, and `selftest` refuses to pass when one stops holding. The
page file is the falsifiable core: a tree frozen into fixed-size records and
read back must walk to the same corpus, whatever history built it.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the band is the order | a node below the root with fewer than `t - 1` keys, or any node above `2t - 1` | every `shape()` walk in the selftest |
| all leaves at one level | a tree that grew jagged | `leaf_levels` on every tree the selftest builds |
| the walk is the corpus | a lost, duplicated, or unsorted key | the walk against `bisect` on a sorted list |
| insertion splits on the way down | a key inserted into a full node | the flood and split tests |
| deletion borrows before it merges | a merge that eats a sibling's only key | the drain and borrow tests |
| the page file reads back identical | a freeze that lies about the tree | `page_pair` after insert AND delete histories |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} load --keys fixtures/keys.txt --order 2
uv run {{ npm_name }} lookup --keys fixtures/keys.txt --key 11
uv run {{ npm_name }} scan --keys fixtures/keys.txt --low 0 --high 50
uv run {{ npm_name }} page --keys fixtures/keys.txt --out tree.page
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `load --keys FILE [--order N] [--json]` | build a tree and walk it in order |
| `lookup --keys FILE --key N [--json]` | whether the tree holds this exact key |
| `scan --keys FILE --low N --high N [--json]` | every key in a window, ascending |
| `page --keys FILE --out FILE [--json]` | freeze the tree, read it back, compare |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

`fixtures/keys.txt` is one integer per line. Blank lines and lines starting
with `#` are skipped. Order is the order `--order N`, the minimum degree:
every node holds `N - 1` to `2N - 1` keys.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was found, or the invariants hold |
| 1 | the key is not held, the window is empty, or an invariant failed |
| 2 | the input cannot be read: a bad file, a bad order, a bad window |

## Files

```
src/{{ package_name }}/btree.py       the tree, the splits, the borrows, the merges
src/{{ package_name }}/page.py        the freeze: fixed-size records, read back identical
src/{{ package_name }}/corpus.py      key lists and a deterministic generator
src/{{ package_name }}/cli.py         the command line
src/{{ package_name }}/selftest.py    the invariants, runnable in a fresh checkout
fixtures/keys.txt                     a corpus the smoke test walks
smoke.sh                              the tool driven the way a user drives it
```

## Non-goals

No strings as keys, no duplicate keys, no persistence beyond the page file,
no concurrent writers, no variable-length nodes. This is a tool for showing
where a B-tree keeps its promises — under insert AND delete histories, not
only after a clean build — not a database.
