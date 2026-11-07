# {{ title }}

{{ description }}

A ring buffer seats integer values in a closed set of slots. The
read cursor and the count are the whole state, the logical contents
are recomputed from `(head, count)` after every operation, and an
over-capacity push overwrites exactly the oldest value — the
drop-oldest policy, stated and proved, never assumed. The buffer
reaches its answers by wrapping; every figure it stores is re-checked
from the slots, never trusted.

## Why

A buffer earns trust the only way a structure can: its drains must
equal a dumb deque's, on every workload, for every question. So this
tool exists to *show* that, not to state it:

```sh
$ {{ npm_name }} drain --values fixtures/values.txt --capacity 8
```

Every claim below is a comparison the selftest computes at run time
against the real modules, and `selftest` refuses to pass when one
stops holding. The falsifiable core is the drain: `brute.py` runs a
stdlib `deque(maxlen=capacity)` with no cursor of its own, and every
order, drop, and cursor position the buffer returns must be the
identical answer.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the drain is the reference deque | a buffer out of order | `contents() == deque(maxlen=n)` on every seeded storm |
| the cursor stays inside `[0, capacity)` | a wrap that escapes the slots | `invariant()` after every push and pop of every storm |
| a full ring drops exactly the oldest | a wrong-slot overwrite | `push()` returns `peek()`, audit clean, every drop |
| the walk is recomputed from (head, count) | stale contents carried over | `contents() == visible sequence` after every op |
| an empty pop is refused | a silent nothing handed back | `RingError` names the empty buffer, state untouched |
| capacity one keeps only the newest | a ring that pretends depth | `peek()` is the last push, overwrites counted |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} drain --values fixtures/values.txt --capacity 8
uv run {{ npm_name }} peek --values fixtures/values.txt --capacity 8
uv run {{ npm_name }} count --values fixtures/values.txt --capacity 8
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `push --values FILE [--capacity N] VALUE` | the buffer with one more value seated |
| `pop --values FILE [--capacity N]` | the oldest value, handed back |
| `peek --values FILE [--capacity N]` | the oldest value, the cursor unmoved |
| `drain --values FILE [--capacity N]` | everything, in order, leaving it empty |
| `count --values FILE [--capacity N]` | capacity, count, and the cursor |
| `demo` | six stories about slots, with real numbers |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

`fixtures/values.txt` is one signed 32-bit integer per line. Blank
lines and lines starting with `#` are skipped; every other line must
be an integer — floats, words, and oversized values are refused by
name. `--capacity` defaults to 8 and must be a positive integer.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the invariants hold |
| 1 | the buffer is empty, a story fails |
| 2 | the input cannot be read: a bad file, a bad value, a bad capacity |

## Files

```
src/{{ package_name }}/ring.py        the buffer, the cursor, the questions
src/{{ package_name }}/values.py      the gate the integers pass
src/{{ package_name }}/brute.py       the deque that is the oracle
src/{{ package_name }}/corpus.py      value lists in, snapshots out
src/{{ package_name }}/storm.py       seeded storms, re-checked per move
src/{{ package_name }}/demo.py        six stories, every claim computed
src/{{ package_name }}/cli.py         the command line
src/{{ package_name }}/selftest.py    the invariants, runnable in a checkout
fixtures/values.txt                   a corpus the smoke test builds on
smoke.sh                              the tool driven the way a user drives it
```

## Non-goals

No floats, no strings-as-values, no values past the signed 32-bit
range, no growable capacity, no blocking producers, no persisted
storage. The buffer is the honest fixed-slot FIFO it is: a tool for
showing what a wrap owes its drain, not a replacement for a queue.
