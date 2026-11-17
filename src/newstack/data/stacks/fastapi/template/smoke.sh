#!/bin/sh
set -eu

if [ -x ./.venv/bin/python ]; then PY=./.venv/bin/python; else PY=${PY:-python3}; fi

echo "smoke: fastapi"
"$PY" -m pytest -q
"$PY" -c "import {{ package_name }}.main as m; print('import ok:', m.app.__class__.__name__)"
echo "smoke: ok"
