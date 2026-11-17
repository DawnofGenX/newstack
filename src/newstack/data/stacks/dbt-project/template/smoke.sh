#!/bin/sh
set -eu

if [ -x ./.venv/bin/dbt ]; then DBT=./.venv/bin/dbt; else DBT=${DBT:-dbt}; fi
if [ -x ./.venv/bin/python ]; then PY=./.venv/bin/python; else PY=${PY:-python3}; fi

echo "smoke: dbt-project"
"$DBT" build --profiles-dir . --no-write-json
"$PY" scripts/check_counts.py
echo "smoke: ok"
