#!/usr/bin/env bash
set -euo pipefail
.venv/bin/python -m pytest
tmp=$(mktemp -d)
printf '[{"id":1,"title":"hello","text":"world of python"}]' | .venv/bin/python -m {{ package_name }} index "$tmp/s.db"
out=$(.venv/bin/python -m {{ package_name }} search "$tmp/s.db" python)
echo "$out"
echo "$out" | grep -q "world"
echo "smoke: PASS"