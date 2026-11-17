#!/bin/sh
set -eu

if [ -x ./.venv/bin/python ]; then PY=./.venv/bin/python; else PY=${PY:-python3}; fi

echo "smoke: python-sse-api"
"$PY" -m pytest -q
"$PY" -c "import {{ package_name }}.counts as c; print('import ok:', c.count_text.__name__ if hasattr(c,'count_text') else 'counts')"
echo "smoke: ok"
