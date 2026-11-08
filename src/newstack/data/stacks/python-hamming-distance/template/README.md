# {{ title }}

{{ description }}

hamming counts the differing bits between two nonnegative integers;
hamming_text counts the differing characters between two equal-length
strings; audit reports any triple whose expected distance does not
match. Out-of-range or malformed inputs are named, never measured.

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} bits 7 11
uv run {{ npm_name }} chars abc axc
uv run {{ npm_name }} audit "7,11,2" "0,0,0"
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `bits A B` | the bit distance between A and B |
| `chars A B` | the char distance between A and B |
| `audit PAIRS` | which pairs fail to round-trip |
| `demo` | six stories about conversion, with real numbers |
| `selftest` | the promises, runnable in a fresh checkout |

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the promises hold |
| 1 | a pair failed to round-trip, a story fails |
| 2 | the input cannot be read: a loud label, a bad value |

## Files

```
src/{{ package_name }}/solve.py          the conversion: hamming, hamming_text, audit
src/{{ package_name }}/demo.py           six stories, every claim computed
src/{{ package_name }}/cli.py            the command line
src/{{ package_name }}/selftest.py       the promises, runnable in a checkout
smoke.sh                                 the tool driven the way a user drives it
```
