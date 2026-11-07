# {{ title }}

{{ description }}

A disjoint-set forest keeps one parent pointer per element and answers a
component question with a walk: two elements share a component exactly
when their walks land on the same name. `union` links the smaller root
under the larger one — a merge rewrites nothing but one pointer, so depth
before any compression stays logarithmic — and `find` compresses the path
on the way back, which rewrites parents toward the root and cannot move an
element to a different component. Deletions are out of scope: a component
that loses a member is a different question, and this forest does not
answer it.

## Why

A forest earns trust by what refuses to break under a seeded workload,
not by asserting it in a comment. So this tool exists to *show* that, not
to state it:

```
$ {{ npm_name }} build --pairs fixtures/pairs.txt
```

Every claim below is a comparison the selftest computes at run time
against the real modules, and `selftest` refuses to pass when one stops
holding. The falsifiable core: after seeded union-only histories the
partition equals a dict-of-parents reference, and a fresh render of the
structure from its (element, root) pairs gives the same partition.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the partition equals the reference | a forest that drifted from a dict-of-parents model | the seeded-workload selftest against `Reference` |
| depth stays logarithmic | a chain longer than `log2(n) + 1` before compression | the size-linked chain tests |
| compression never moves a component | a `find` that answers a different root | partition-equal-before-and-after on compressed walks |
| union is idempotent | a repeat merge that changes the partition | the ten-repeat tests |
| the render rebuilds the partition | a snapshot that lies about the forest | `from_snapshot(snapshot())` round trips |
| one name per element | an element answering to two roots | the refused-render tests |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} build --pairs fixtures/pairs.txt
uv run {{ npm_name }} connected --pairs fixtures/pairs.txt --first 1 --second 7
uv run {{ npm_name }} count --pairs fixtures/pairs.txt
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `build --pairs FILE [--json]` | join a workload, list the partition |
| `add --pairs FILE --element N [--json]` | whether an element opens a new component |
| `union --pairs FILE --first N --second N [--json]` | whether a merge changes anything |
| `connected --pairs FILE --first N --second N [--json]` | whether two walks share a name |
| `components --pairs FILE [--json]` | enumerate every component |
| `count --pairs FILE [--json]` | how many components the workload leaves |
| `demo [--json]` | a fixed forest, stated plainly |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

`fixtures/pairs.txt` is one `a b` pair per line. Blank lines and lines
starting with `#` are skipped. Elements are integers; every element in a
pair must also appear as some pair member, and deletions are out of scope.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was found, or the invariants hold |
| 1 | the answer was no: separate elements, an already-open element, a no-op merge, or a failed invariant |
| 2 | the input cannot be read: a bad file, a bad pair, an outsider element |

## Files

```
src/{{ package_name }}/forest.py      the forest, the links, the compression
src/{{ package_name }}/pairs.py       workload files and a deterministic generator
src/{{ package_name }}/cli.py         the command line
src/{{ package_name }}/selftest.py    the invariants, runnable in a fresh checkout
fixtures/pairs.txt                    a workload the smoke test drives
smoke.sh                              the tool driven the way a user drives it
```

## Non-goals

No deletions — a component that loses a member is out of scope and the
forest says so rather than half-answering. No strings as elements, no
weighted unions beyond size, no persistence, no concurrent writers. This
is a tool for showing where a disjoint-set forest keeps its promises —
partition equality, logarithmic depth, idempotent merges — not a database.
