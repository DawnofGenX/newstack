# {{ title }}

{{ description }}

The scanner weighs a sliding window with a documented base and
modulus, rolls it one letter at a time — subtract the outgoing
letter, shift, add the incoming one — and *still* checks every
candidate letter by letter. Overlaps are counted, not skipped:
`ana` inside `banana` starts twice. The promise is checked, never
assumed: every start list equals the naive scan's, exactly.

## Why

A matcher earns trust the only way a matcher can: its starts must
equal a dumb scan's, on every pattern, for every text — and its
roll must equal a fresh weigh, window after window. So this tool
exists to *show* that, not to state it:

```sh
$ {{ npm_name }} find --pattern ana banana
```

Every claim below is a comparison the selftest computes at run time
against the real modules, and `selftest` refuses to pass when one
stops holding. The falsifiable core is the start list: `naive.py`
tries every position with no hash at all, and every start the
rolling scan reports must be the identical list.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the starts are the naive scan's | a scan that misses or invents | start lists equal on seeded text/pattern corpora |
| the roll equals the fresh weigh | an update that dropped a letter | rolled digests equal `window_hash` on shipped windows |
| collisions are honest | a digest that answered for the letters | every candidate checked letter by letter |
| overlaps are counted | a hit that swallows the next | `ana` in `banana` starts at 1 and 3 |
| the empty pattern is honest | a special case invented away | it sits at every position, count `len(text) + 1` |
| a long pattern never sits | a scan past the text's end | patterns longer than the text return nothing |
| loud strings are refused | uppercase, digits, spaces | the gate names the string, no window is hashed |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} find --pattern ana "banana"
uv run {{ npm_name }} count --pattern ana "banana"
uv run {{ npm_name }} digest --pattern abra
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `find --pattern PATTERN TEXT` | every start in order, overlaps kept |
| `count --pattern PATTERN TEXT` | how many starts the text owes |
| `digest --pattern PATTERN` | the documented hash, base, and modulus |
| `demo` | six stories about windows, with real numbers |
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
src/{{ package_name }}/hashing.py      the base, the modulus, the roll, the weigh
src/{{ package_name }}/scanner.py      the rolling scan and its collision tax
src/{{ package_name }}/pattern.py      the gate the strings pass
src/{{ package_name }}/naive.py        the hashless scan that is the oracle
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
no regex, no case-folding, no persisted storage, no streaming text,
no double hashing. The scanner is the honest Rabin-Karp it is: a
tool for showing what a rolling window promises a scan, not a
replacement for `str.find`.
