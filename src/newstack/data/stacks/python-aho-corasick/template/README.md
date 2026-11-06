# {{ title }}

{{ description }}

## What it is

An Aho-Corasick automaton is a trie over the patterns plus failure links
built breadth-first: a state that stops matching mid-pattern fails forward
to a shorter suffix that is still a prefix of something, never backward. A
state reports the patterns ending on it *and* every pattern ending on its
failure chain, which is how `he` is still reported inside `she`. One pass
over the text reports every `(pattern, end-position)` pair; the naive scan
needs one walk per pattern.

## Why

A multi-pattern scanner earns trust the same way any scanner does: by
agreeing with the dumb one. The falsifiable core here is an equality, not a
benchmark — on seeded random alphabets the sweep's hit set is *exactly* the
naive per-pattern scan's, overlaps included, and the selftest recomputes
that against the real modules on every run. The counter story sits beside
it: the shipped prose corpus reports the same hits either way, but the
sweep crosses fewer states than the naive scanner inspects windows.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| one sweep, no rewinding | a scanner that re-reads a character | `sweep()` walks `enumerate(text)` once |
| suffix outputs are hits | `he` lost inside `she` | the textbook `ahishers` ledger |
| equal to the naive scan | a hit the automaton invented or lost | seeded alphabets in the selftest and tests |
| duplicates stated once | the same pattern hunting twice | `patterns` and `count` on `ab,ab,ab` |
| edges answer plainly | a crash on no patterns, or no text | the degenerate section of the selftest |
| the ledger is sorted | a report that shuffles its hits | end, then start, then pattern, everywhere |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} build --patterns fixtures/patterns.txt
uv run {{ npm_name }} scan --patterns fixtures/patterns.txt --text fixtures/patterns.txt
uv run {{ npm_name }} count --patterns fixtures/patterns.txt --text fixtures/patterns.txt
uv run {{ npm_name }} demo
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `build --patterns FILE [--json]` | state the automaton: patterns, states, depth |
| `scan --patterns FILE --text FILE [--json]` | every `(pattern, end)` hit, sorted |
| `count --patterns FILE --text FILE [--json]` | hits plus the sweep-vs-naive ledger |
| `demo` | the counter story on the shipped corpus |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

`fixtures/patterns.txt` is one pattern per line; blank lines and `#`
comments are skipped. Duplicate patterns are deduped at build time — a
pattern stated twice is one pattern, and it still reports once per match.
An empty pattern set is legal and sweeps to nothing. A blank pattern is
refused: it would match at every boundary. Texts are read verbatim.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | hits were found, or the invariants hold |
| 1 | the sweep found no hits, or an invariant failed |
| 2 | the input cannot be read: a bad file, a blank pattern, a bad shape |

## Files

```
src/{{ package_name }}/automaton.py   the trie, the BFS failure links, the sweep
src/{{ package_name }}/naive.py       the reference scan, honestly counted
src/{{ package_name }}/corpus.py      pattern lists, texts, seeded generators
src/{{ package_name }}/cli.py         the command line
src/{{ package_name }}/selftest.py    the invariants, runnable in a fresh checkout
fixtures/patterns.txt                 the textbook set the smoke test sweeps
smoke.sh                              the tool driven the way a user drives it
```

## Non-goals

No case folding, no unicode folding, no anchored or wildcard patterns, no
streaming rebuilds, no replacement of `str.find` for one lone needle. This
is a tool for showing where a one-pass automaton keeps its promises — every
overlap, in a stated order, equal to the scan everyone trusts — not a
search engine.
