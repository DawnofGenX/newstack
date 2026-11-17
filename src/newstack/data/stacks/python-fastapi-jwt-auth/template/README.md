# {{ title }}

{{ description }}

## Run

```bash
uv venv --allow-existing .venv
uv pip install -e .
JWT_SECRET=change-me uvicorn {{ package_name }}.main:app --reload
```

## Test

```bash
uv run pytest
python -m {{ package_name }} --selftest
bash smoke.sh
```