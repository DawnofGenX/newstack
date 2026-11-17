#!/bin/sh
set -eu

if [ -x ./.venv/bin/python ]; then PY=./.venv/bin/python; else PY=${PY:-python3}; fi

echo "smoke: python-fastapi-sqlite"
"$PY" -c "from {{ package_name }}.db import connect, migrate; c = connect(':memory:'); first = migrate(c); second = migrate(c); assert first == ['001_notes.sql'], first; assert second == [], second; print('migrations applied once:', first)"
"$PY" -m pytest -q
echo "smoke: ok"
