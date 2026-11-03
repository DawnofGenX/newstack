# {{ title }}

{{ description }}

A small pandas workspace: typed DataFrame helpers in `src/{{ package_name }}/`, tests that
build their own frames, ruff with a pinned rule set, and a scratch notebook.

## Getting started

```bash
uv sync
```

## Tests

```bash
uv run pytest
```

## Lint

```bash
uv run ruff check .
```

## Notebook

```bash
uv run jupyter lab notebooks/
```

`notebooks/explore.ipynb` imports the package and calls `summarize` on a three-row frame —
useful as a smoke test that the installed package and pandas agree.

## Layout

```
src/{{ package_name }}/data.py   summarize() and clean()
tests/test_data.py               pytest coverage for both helpers
notebooks/explore.ipynb          scratch exploration
```
