# {{ title }}

{{ description }}

A count-min sketch over the fixed universe `[0, 256)`: five
deterministic multiplicative rows of 256 cells, an answer that is
the min of the rows a key visits, and an audit after every update
that the min never dips under the ledger truth. With the shipped
configuration the rows are bijections the universe cannot crowd, so
on the shipped corpora the answers equal the ledger exactly; on a
narrow grid they drift upward, never under.

## Why

A sketch earns trust the only way a counter can: its answers must
sit at or above the truth on every stream, and the min must stay the
min. So this tool exists to *show* that, not to state it:

```sh
$ {{ npm_name }} count --stream fixtures/stream.txt 7
```

Every claim below is a comparison the selftest computes at run time
against the real modules, and `selftest` refuses to pass when one
stops holding. The falsifiable core is `brute.py`: a plain dict
summed with no structure at all, and a min read straight off the
raw grid. The sketch cannot grade its own homework from there.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the min of rows never dips under the truth | an undercount | `audit()` runs after every `add`, on every seeded stream |
| an empty sketch counts zero | a phantom count | `count(key) == 0` on every fresh grid |
| same seed, same answers | a drift in the replay | twin streams answer identically, cell for cell |
| the min, not the max, answers | a promise flipped | a drifting 48-wide grid still answers the ledger |
| the shipped grid answers exactly | a drift sold as honest | every shipped corpus counts equal to its ledger |
| noise is refused by name | a silent bad event | off-universe keys and malformed streams exit 2 |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} count --stream fixtures/stream.txt 7
uv run {{ npm_name }} add --stream fixtures/stream.txt 7 2
uv run {{ npm_name }} report --stream fixtures/stream.txt
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `add --stream FILE KEY [N]` | the ledger with n more for key, audited |
| `count --stream FILE KEY` | the min of the rows the key visits |
| `report --stream FILE` | width, depth, rows, tracked, total, drift |
| `seed --count N --seed S` | a deterministic stream, printed |
| `demo` | six stories about counts, with real numbers |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

`fixtures/stream.txt` is one `key n` pair per line: keys on
`[0, 256)`, counts positive. Blank lines and lines starting with `#`
are skipped; every other line must be a pair — floats, lone numbers,
third columns, and off-universe keys are refused by name.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the invariants hold |
| 1 | the key was never tracked by this stream |
| 2 | the input cannot be read: a bad file, a bad key, a bad count |

## Files

```
src/{{ package_name }}/sketch.py     the rows, the min, the audit per add
src/{{ package_name }}/hashes.py     the multiplicative rows, bijections
src/{{ package_name }}/keys.py       the gate the universe passes
src/{{ package_name }}/brute.py      the ledger and the raw min, the oracles
src/{{ package_name }}/corpus.py     streams in, snapshots out
src/{{ package_name }}/workload.py   seeded streams, re-audited per update
src/{{ package_name }}/demo.py       six stories, every claim computed
src/{{ package_name }}/cli.py        the command line
src/{{ package_name }}/selftest.py   the invariants, runnable in a checkout
fixtures/stream.txt                  a corpus the smoke test builds on
smoke.sh                             the tool driven the way a user drives it
```

## Honest edges

The exactness is a property of the shipped shape, not of the idea:
256 cells with odd multipliers are permutations, so a 256-wide
sketch over a 256-wide universe never collides. Shrink the width
and drift returns — upward only. No decrement, no eviction, no
persisted storage, no concurrent mutators, no float counts, no
keys off `[0, 256)`.
