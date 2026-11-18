# {{ title }}

{{ description }}

Requires Python {{ python_version }} or newer.

## Run

```bash
uv venv --allow-existing .venv && uv pip install -e . pytest ruff
.venv/bin/python -m {{ package_name }} tables fixtures/sample.html
```

## Check

```bash
.venv/bin/python -m {{ package_name }} --selftest
.venv/bin/python -m pytest
bash smoke.sh
```

## Traps this starter already paid for

- Parsing uses the stdlib html.parser backend, so no lxml install is required.
- Table headers are inferred when the first row is all `<th>`.
- Missing cells are padded so rows stay rectangular.
- Cards are selected with the `.card` CSS selector.
