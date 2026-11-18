# {{ title }}

{{ description }}

Requires Python {{ python_version }} or newer.

## Run

```bash
uv venv --allow-existing .venv && uv pip install -e . pytest ruff
.venv/bin/python -m {{ package_name }} revenue --data data/orders.csv
```

## Check

```bash
.venv/bin/python -m {{ package_name }} --selftest
.venv/bin/python -m pytest
bash smoke.sh
```

## Traps this starter already paid for

- CSV is read with DuckDB's `read_csv_auto`, so types are inferred.
- Queries run in an in-memory database; no persistent state.
- `--data` overrides the bundled fixture path.
- Results are emitted as JSON for easy piping.
