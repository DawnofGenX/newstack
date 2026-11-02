# {{ title }}

{{ description }}

A single-command CLI built on the standard library — no runtime dependencies.

## Install

```bash
uv sync
uv run {{ npm_name }} --help
```

Or install it on your PATH:

```bash
uv tool install .
{{ npm_name }} greet --name world
```

## Commands

```text
{{ npm_name }} greet --name <name>   print a greeting
{{ npm_name }} --version             print the version
```

## Develop

```bash
uv run pytest
uv run ruff check .
```

Generated with [newstack](https://github.com/DawnofGenX/newstack).
