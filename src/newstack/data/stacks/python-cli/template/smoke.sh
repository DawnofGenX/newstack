#!/bin/sh
set -eu

if [ -x ./.venv/bin/python ]; then PY=./.venv/bin/python; else PY=${PY:-python3}; fi

echo "smoke: python-cli"
"$PY" -m {{ package_name }} --version
"$PY" -m {{ package_name }} greet --name smoke
"$PY" -m pytest -q
echo "smoke: ok"
