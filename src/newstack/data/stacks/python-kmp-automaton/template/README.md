# {{ title }}

{{ description }}

The automaton builds a failure table from a pattern — the longest
proper border of every prefix, the naive border count computed once
— and rides the text letter by letter, falling back along those
links instead of rewinding. Overlaps are counted, not skipped:
`ana` inside `banana` starts twice. The promise is checked, never
assumed: every start list equals the naive scan's, exactly.

## Why

A matcher earns trust the only way a matcher can: its starts must
equal a dumb scan's, on every pattern, for every text — and its
table must equal the border count, state by state. So this tool
exists to *show* that, not to state it:

```sh
$ {{ npm_name }} find --pattern ana banana
```

Every claim below is a comparison the selftest computes at run time
against the real modules, and `selftest` refuses to pass when one
stops holding. The falsifiable core is the start list: `naive.py`
tries every position with no cleverness at all, and every start the
automaton reports must be the identical list.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the starts are the naive scan's | a scan that misses or invents | start lists equal on seeded text/pattern corpora |
| the table is the border count | a link that forgot a border | `table[k] == border(pattern[:k])` on shipped patterns |
| overlaps are counted | a hit that swallows the next | `ana` in `banana` starts at 1 and 3 |
| the empty pattern is honest | a special case invented away | it sits at every position, count `len(text) + 1` |
| a long pattern never sits | a scan past the text's end | patterns longer than the text return nothing |
| loud strings are refused | uppercase, digits, spaces | the gate names the string, no table is built |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} find --pattern ana "banana"
uv run {{ npm_name }} count --pattern ana "banana"
uv run {{ npm_name }} table --pattern anana
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `find --pattern PATTERN TEXT` | every start in order, overlaps kept |
| `count --pattern PATTERN TEXT` | how many starts the text owes |
| `table --pattern PATTERN` | the failure table, state by state |
| `demo` | six stories about scans, with real numbers |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

Patterns and texts are lowercase ASCII letters only; the empty
pattern and the empty text are legal. `fixtures/patterns.txt` is one
pattern per line; blank lines and lines starting with `#` are
skipped, and every other line must pass the gate.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the invariants hold |
| 1 | the pattern never sits, a story fails |
| 2 | the input cannot be read: a loud string, a bad file |

## Files

```
src/{{ package_name }}/automaton.py    the table, the scan, the questions
src/{{ package_name }}/pattern.py      the gate the strings pass
src/{{ package_name }}/naive.py        the border and the scan that are the oracle
src/{{ package_name }}/corpus.py       pattern lists in, snapshots out
src/{{ package_name }}/workload.py     seeded storms, start against start
src/{{ package_name }}/demo.py         six stories, every claim computed
src/{{ package_name }}/cli.py          the command line
src/{{ package_name }}/selftest.py     the invariants, runnable in a checkout
fixtures/patterns.txt                  a corpus the smoke test builds on
smoke.sh                               the tool driven the way a user drives it
```

## Non-goals

No uppercase, no digits, no spaces, no Unicode beyond ASCII letters,
no regex, no case-folding, no persisted storage, no streaming text.
The automaton is the honest Knuth-Morris-Pratt scan it is: a tool
for showing what a failure table promises a scan, not a replacement
for `str.find`.
