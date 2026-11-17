# {{ title }}

{{ description }}

## Run

```bash
uv venv --allow-existing .venv
uv pip install -e .
PORT=8080 .venv/bin/python -m {{ package_name }}
```

## Test

```bash
.venv/bin/python -m pytest
.venv/bin/python -m {{ package_name }} --selftest
bash smoke.sh
```