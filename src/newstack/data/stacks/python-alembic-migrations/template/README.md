# {{ title }}

{{ description }}

## Upgrade

```bash
uv venv --allow-existing .venv
uv pip install -e .
.venv/bin/alembic upgrade head
```

## Test

```bash
.venv/bin/python -m pytest
.venv/bin/python -m {{ package_name }} --selftest
bash smoke.sh
```