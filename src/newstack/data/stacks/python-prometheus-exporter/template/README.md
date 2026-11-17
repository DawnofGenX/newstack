# {{ title }}

{{ description }}

## Run

```bash
uv venv --allow-existing .venv
uv pip install -e .
PORT=9090 .venv/bin/python -m {{ package_name }}
curl http://127.0.0.1:9090/metrics
```

## Test

```bash
.venv/bin/python -m pytest
.venv/bin/python -m {{ package_name }} --selftest
bash smoke.sh
```