#!/bin/sh
set -eu

if [ -x ./.venv/bin/python ]; then PY=./.venv/bin/python; else PY=${PY:-python3}; fi
if command -v uv >/dev/null 2>&1; then RUN="uv run"; else RUN=""; fi

echo "smoke: mkdocs-site"
if [ -n "$RUN" ]; then
  uv run mkdocs build --strict
  uv run python tools/check_fences.py docs
  uv run pytest
else
  "$PY" -m mkdocs build --strict
  "$PY" tools/check_fences.py docs
  "$PY" -m pytest -q
fi
echo "smoke: ok"
