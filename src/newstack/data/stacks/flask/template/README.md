# {{ title }}

{{ description }}

A small Flask application built around an application factory: `create_app()`
wires a blueprint of JSON routes, so tests get a fresh app per test instead of
sharing one global instance.

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
uv sync
```

## Run

```bash
uv run flask --app app run --debug
```

Then:

```bash
curl http://127.0.0.1:5000/health   # {"status":"ok"}
curl http://127.0.0.1:5000/items    # []
```

## Test

```bash
uv run pytest
```

## Lint

```bash
uv run ruff check .
```

## Layout

```
app/__init__.py     create_app() factory
app/routes.py       /health and /items blueprints
tests/test_routes.py fixtures + route tests
```
