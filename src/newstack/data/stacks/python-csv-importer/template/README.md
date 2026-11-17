# {{ project_name }}

{{ description }}

## Run

```bash
uv venv --allow-existing .venv && uv pip install -e .
.venv/bin/python -m {{ package_name }} data.csv out.db --dry-run
.venv/bin/python -m {{ package_name }} data.csv out.db
```

## Tests

```bash
uv run pytest
```