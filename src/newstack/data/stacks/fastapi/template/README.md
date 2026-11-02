# {{ title }}

{{ description }}

A small typed JSON API: `GET /health`, `GET /items`, `POST /items`, `GET /items/{item_id}`.

## Run

```bash
uv sync
uv run uvicorn {{ package_name }}.main:app --reload
```

Then open <http://127.0.0.1:8000/docs> for the interactive OpenAPI docs.

## Test

```bash
uv run pytest
uv run ruff check .
```

## Docker

```bash
docker build -t {{ npm_name }} .
docker run -p 8000:8000 {{ npm_name }}
```

Generated with [newstack](https://github.com/DawnofGenX/newstack).
