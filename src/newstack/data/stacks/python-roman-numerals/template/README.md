# {{ title }}

{{ description }}

int_to_roman turns a positive integer into its letter form;
roman_to_int reads a roman string back into an integer; audit
reports any pair that does not round-trip. Out-of-range or malformed
inputs are named, never converted.

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} encode 10
uv run {{ npm_name }} decode X
uv run {{ npm_name }} audit "10,X" "42,XLII"
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `encode N` | the roman string for N |
| `decode S` | the integer value of roman string S |
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
src/{{ package_name }}/solve.py          the conversion: int_to_roman, roman_to_int, audit
src/{{ package_name }}/demo.py           six stories, every claim computed
src/{{ package_name }}/cli.py            the command line
src/{{ package_name }}/selftest.py       the promises, runnable in a checkout
smoke.sh                                 the tool driven the way a user drives it
```
