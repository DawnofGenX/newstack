#!/bin/sh
# Smoke test: run the project's real entry points.
set -eu

if [ -x ./.venv/bin/python ]; then PY=./.venv/bin/python; else PY=${PY:-python3}; fi

echo "smoke: data-science"
"$PY" -m pytest -q
"$PY" -c "import {{ package_name }}.data as d; print('import ok:', d.clean.__name__, d.summarize.__name__)"
echo "smoke: ok"
