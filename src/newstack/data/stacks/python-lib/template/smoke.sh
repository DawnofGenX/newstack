#!/bin/sh
set -eu

if [ -x ./.venv/bin/python ]; then PY=./.venv/bin/python; else PY=${PY:-python3}; fi

echo "smoke: python-lib"
"$PY" -m pytest -q
"$PY" -c "import {{ package_name }}; print('import ok:', {{ package_name }}.__version__); from {{ package_name }} import word_count, truncate; assert word_count('hello world') == 2; assert truncate('hello world', 8) == 'hello w…'; print('core ok')"
echo "smoke: ok"
