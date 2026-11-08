# {{ title }}

{{ description }}

A double-ended queue of integers, both ends first-class.

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} make 1 2 3
uv run {{ npm_name }} rotate 1 1 2 3
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `make VALUES` | build a deque |
| `append VALUES` | append right |
| `appendleft VALUES` | append left |
| `pop VALUES` | pop right |
| `popleft VALUES` | pop left |
| `peek VALUES` | peek right |
| `peekleft VALUES` | peek left |
| `rotate STEPS VALUES` | rotate |
| `tolist VALUES` | list contents |
| `demo` | six stories |
| `selftest` | the promises |

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | answer given, or promises hold |
| 1 | a story fails |
| 2 | input cannot be read |
