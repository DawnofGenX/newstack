# {{ title }}

{{ description }}

## Run

```bash
uv venv --allow-existing .venv
uv pip install -e .
.venv/bin/python -m {{ package_name }} --ticks 10
```

## Test

```bash
.venv/bin/python -m pytest
.venv/bin/python -m {{ package_name }} --selftest
bash smoke.sh
```