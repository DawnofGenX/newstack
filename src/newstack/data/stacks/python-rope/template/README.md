# {{ title }}

{{ description }}

A rope is a binary tree whose leaves hold short chunks of text and whose
internal nodes cache the length of everything below them. `insert`,
`delete`, `slice`, and `append` walk to the seam, split one leaf, and
recompute only the cached lengths along the path they touched; `concat`
pairs two ropes without visiting either. `to_string` is literally
`"".join` of the leaves in order, and `rebalance` rebuilds the shape over
the same chunks — balance is invisible, the text never notices.

## Why

A rope earns its name by what stays true under a seeded edit workload, not
by asserting it in a comment. So this tool exists to *show* that, not to
state it:

```
$ {{ npm_name }} load --text fixtures/text.txt
```

Every claim below is a comparison the selftest computes at run time against
the real modules, and `selftest` refuses to pass when one stops holding.
The falsifiable core: on a seeded edit script a plain `str` carries the
same window every slice and length answer must match, and the edit counter
tracks the height of the spine, never the length of the text — a walk
through 20,000 characters touches a rounding error of nodes where a
`str` rebuild copies the whole text.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| to_string is the join | a chunk lost, duplicated, or reordered | every `to_string` against `"".join(chunks())` |
| edits answer like the str | a slice or length disagreeing with the shelf | the seeded workloads in the selftest |
| balance is invisible | a rebuild that changes the text | `rebalance` before/after on grown ropes |
| split rejoins exactly | a cut whose halves concat to something else | split/concat at every edge offset |
| cost tracks the spine | an edit whose touches scale with the text | the counter story over 20k+ ropes |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} load --text fixtures/text.txt
uv run {{ npm_name }} slice --text fixtures/text.txt --start 6 --stop 11
uv run {{ npm_name }} join --text fixtures/text.txt --other fixtures/text.txt
uv run {{ npm_name }} split --text fixtures/text.txt --at 40
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `load --text FILE [--json]` | read a text and show its spine |
| `slice --text FILE --start N --stop N [--json]` | a window as a rope |
| `join --text FILE --other FILE [--json]` | concat two texts, no copying |
| `split --text FILE --at N [--json]` | cut, concat back, compare |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

`fixtures/text.txt` is one line per paragraph. Blank lines and lines
starting with `#` are skipped; the surviving lines join by newlines. A
rope built from any text answers exactly what that text answers.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was found, or the invariants hold |
| 1 | the window is empty, or a rejoin disagreed |
| 2 | the input cannot be read: a bad file, a bad window, a bad leaf |

## Files

```
src/{{ package_name }}/rope.py        the tree, the cached lengths, the walks
src/{{ package_name }}/corpus.py      text documents and a deterministic generator
src/{{ package_name }}/cli.py         one question per run, 0/1/2 answers
src/{{ package_name }}/selftest.py    the invariants, runnable in a checkout
fixtures/text.txt                     the corpus the smoke test walks
```
