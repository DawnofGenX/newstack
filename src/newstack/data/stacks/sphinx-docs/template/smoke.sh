#!/bin/sh
set -eu

if [ -x ./.venv/bin/python ]; then PY=./.venv/bin/python; else PY=${PY:-python3}; fi

echo "smoke: sphinx-docs"
"$PY" -m sphinx -W --keep-going -q -b html docs docs/_build/html
"$PY" -m sphinx -q -b doctest docs docs/_build/doctest
"$PY" -m pytest -q
echo "smoke: ok"
