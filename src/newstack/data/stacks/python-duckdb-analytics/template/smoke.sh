#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
PY="$ROOT/.venv/bin/python"

"$PY" -m {{ package_name }} revenue --data "$ROOT/data/orders.csv" | "$PY" -c "import sys; v=float(sys.stdin.read()); assert v==640.0, v"
"$PY" -m {{ package_name }} top-n 2 --data "$ROOT/data/orders.csv" | "$PY" -c "import sys,json; d=json.load(sys.stdin); assert d[0]['product']=='gadget' and d[0]['revenue']==370, d"

echo "smoke: all checks passed"
