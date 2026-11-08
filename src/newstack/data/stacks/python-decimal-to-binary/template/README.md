# {{ title }}

{{ description }}

dec_to_binary turns a nonnegative integer into its base-two digits;
binary_to_decimal reads a binary string back into an integer; audit
reports any pair that does not round-trip. Oversized or malformed
inputs are named, never converted.

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} convert 10
uv run {{ npm_name }} read 1010
uv run {{ npm_name }} audit "10,1010" "7,111"
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `convert N` | the binary string for N |
| `read S` | the decimal value of binary string S |
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
src/{{ package_name }}/solve.py          the conversion: dec_to_binary, binary_to_decimal, audit
src/{{ package_name }}/demo.py           six stories, every claim computed
src/{{ package_name }}/cli.py            the command line
src/{{ package_name }}/selftest.py       the promises, runnable in a checkout
smoke.sh                                 the tool driven the way a user drives it
```