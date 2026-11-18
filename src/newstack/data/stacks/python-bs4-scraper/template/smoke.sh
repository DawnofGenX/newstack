#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
PY="$ROOT/.venv/bin/python"

out=$("$PY" -m {{ package_name }} tables "$ROOT/fixtures/sample.html")
echo "$out" | "$PY" -c "import sys,json; d=json.load(sys.stdin); assert sum(len(t) for t in d)==3, d" || { echo "FAIL table count"; exit 1; }

cards=$("$PY" -m {{ package_name }} cards "$ROOT/fixtures/sample.html")
echo "$cards" | "$PY" -c "import sys,json; d=json.load(sys.stdin); assert len(d)==2, d" || { echo "FAIL card count"; exit 1; }

echo "smoke: all checks passed"
