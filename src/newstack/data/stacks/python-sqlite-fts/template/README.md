# {{ title }}

{{ description }}

## Run

```bash
uv venv --allow-existing .venv
uv pip install -e .
echo '[{"id":1,"title":"hello","text":"world"}]' | .venv/bin/python -m {{ package_name }} index ./search.db
.venv/bin/python -m {{ package_name }} search ./search.db hello
```