#!/bin/sh
set -eu

if [ -x ./.venv/bin/python ]; then PY=./.venv/bin/python; else PY=${PY:-python3}; fi

echo "smoke: flask"
"$PY" -m pytest -q
"$PY" -c "import app; print('import ok:', app.create_app().__class__.__name__)" 2>/dev/null || "$PY" -c "import app.routes; print('import ok: routes')"
echo "smoke: ok"
