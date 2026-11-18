# {{ title }}

{{ description }}

Requires Python {{ python_version }} or newer.

## Run

```bash
uv venv --allow-existing .venv && uv pip install -e . pytest ruff
.venv/bin/python -m {{ package_name }} add "buy milk"
.venv/bin/python -m {{ package_name }} list
```

## Check

```bash
.venv/bin/python -m {{ package_name }} --selftest
.venv/bin/python -m pytest
bash smoke.sh
```

## Traps this starter already paid for

- Typer app object is the console entry point, so `python -m` and the installed script both work.
- Task data is stored as JSON in the current directory (`tasks.json`) by default; override with `--file`.
- IDs are monotonic and never reused after removal.
- ruff target version is derived from the declared Python floor.
