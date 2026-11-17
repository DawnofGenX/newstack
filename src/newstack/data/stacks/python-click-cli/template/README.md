# {{ title }}

{{ description }}

Requires Python {{ python_version }} or newer.

## Run

```bash
uv venv --allow-existing .venv && uv pip install -e . pytest ruff
.venv/bin/python -m {{ package_name }} greet --name you
```

## Check

```bash
.venv/bin/python -m {{ package_name }} --selftest
.venv/bin/python -m pytest
.venv/bin/ruff check .
```