# {{ title }}

{{ description }}

## Run

```bash
uv venv --allow-existing .venv
uv pip install -e .
.venv/bin/python -m {{ package_name }} validate ./schema.json ./doc.json --json
```