#!/bin/sh
set -eu

if [ -x ./.venv/bin/python ]; then PY=./.venv/bin/python; else PY=${PY:-python3}; fi

echo "smoke: python-scheduler-api"
"$PY" -c "from {{ package_name }}.db import connect, migrate; c = connect('/tmp/newstack-scheduler-smoke.db'); assert migrate(c) == ['001_jobs.sql']; assert migrate(c) == []; c.close(); import os; os.remove('/tmp/newstack-scheduler-smoke.db')"
"$PY" -m pytest -q
echo "smoke: ok"
