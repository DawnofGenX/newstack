#!/usr/bin/env bash
set -euo pipefail
.venv/bin/python -m pytest
tmp=$(mktemp -d)
printf 'product,qty,price\npen,2,1.5\ncup,3,2.0\n' > "$tmp/data.csv"
.venv/bin/python -m {{ package_name }} report "$tmp/data.csv" "$tmp/report.xlsx"
test -f "$tmp/report.xlsx"
echo "smoke: PASS"