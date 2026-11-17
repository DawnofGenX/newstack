# {{ project_name }}

{{ description }}

GraphQL on `graphql-core` with a stdlib `http.server` backend. No web framework.

## Run

```bash
uv venv --allow-existing .venv && uv pip install -e .
PORT=8080 .venv/bin/python -m {{ package_name }}
curl -s http://127.0.0.1:8080/health
curl -s -X POST http://127.0.0.1:8080/graphql -H 'content-type: application/json' \
  -d '{"query":"{ hello add(a: 2, b: 3) }"}'
```

## Tests

```bash
uv run pytest
```