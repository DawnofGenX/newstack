# {{ title }}

{{ description }}

The array cuts a word by the prefix every suffix shares — `z[i]` is
the longest common prefix of the word and the word from `i` on,
`z[0]` the whole length — and the derived occurrence list rides the
concatenated array. Overlaps are counted, not skipped: `ana` inside
`banana` starts twice. The promise is checked, never assumed: every
array equals the naive per-position scan's, exactly.

## Why

An array earns trust the only way an array can: its entries must
equal a dumb stepper's, on every word — and its occurrences must
equal a dumb scan's starts, on every pattern. So this tool exists to
*show* that, not to state it:

```sh
$ {{ npm_name }} zarray --word anana
```

Every claim below is a comparison the selftest computes at run time
against the real modules, and `selftest` refuses to pass when one
stops holding. The falsifiable core is the array: `naive.py` steps
two words letter by letter with no cleverness at all, and every
entry the window writes must be the identical number.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the array is the stepper's answer | an entry that misses or invents | array equal to the naive LCP scan on seeded corpora |
| z[0] is the length of the word | a seat invented away | `z[0] == len(word)`, the empty word owns the empty array |
| the occurrences are the scan's starts | a sitting missed or invented | concatenated-array starts equal the naive starts |
| overlaps are counted | a hit that swallows the next | `ana` in `banana` starts at 1 and 3 |
| the empty word is honest | a special case invented away | it owns the empty array; the empty pattern sits everywhere |
| loud strings are refused | uppercase, digits, spaces | the gate names the string, no array is cut |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} zarray --word anana
uv run {{ npm_name }} occurrences --pattern ana "banana"
uv run {{ npm_name }} count --pattern ana "banana"
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `zarray --word WORD` | the array of the word, z[0] the length |
| `occurrences --pattern PATTERN WORD` | every start, the concatenated array's answer |
| `count --pattern PATTERN WORD` | how many starts the word owes |
| `demo` | six stories about arrays, with real numbers |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

Words and patterns are lowercase ASCII letters only; the empty word
is legal. `fixtures/words.txt` is one word per line; blank lines and
lines starting with `#` are skipped, and every other line must pass
the gate.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the invariants hold |
| 1 | the pattern never sits, a story fails |
| 2 | the input cannot be read: a loud string, a bad file |

## Files

```
src/{{ package_name }}/array.py        the window, the array, the derived starts
src/{{ package_name }}/word.py         the gate the strings pass
src/{{ package_name }}/naive.py        the stepper and the scan that are the oracle
src/{{ package_name }}/corpus.py       word lists in, snapshots out
src/{{ package_name }}/workload.py     seeded storms, entry against entry
src/{{ package_name }}/demo.py         six stories, every claim computed
src/{{ package_name }}/cli.py          the command line
src/{{ package_name }}/selftest.py     the invariants, runnable in a checkout
fixtures/words.txt                     a corpus the smoke test builds on
smoke.sh                               the tool driven the way a user drives it
```

## Non-goals

No uppercase, no digits, no spaces, no Unicode beyond ASCII letters,
no regex, no case-folding, no persisted storage, no streaming text.
The array is the honest linear scan it is: a tool for showing what a
window promises an entry, not a replacement for `str.find`.
