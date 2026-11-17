#!/bin/sh
set -eu

if [ -x ./.venv/bin/python ]; then PY=./.venv/bin/python; else PY=${PY:-python3}; fi

echo "smoke: django"
"$PY" manage.py check
"$PY" manage.py makemigrations --check --dry-run
"$PY" -m pytest -q
echo "smoke: ok"
