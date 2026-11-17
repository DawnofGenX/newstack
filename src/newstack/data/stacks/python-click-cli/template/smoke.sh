#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
PY="$ROOT/.venv/bin/python"

"$PY" -m {{ package_name }} greet --name smoke | grep -q "hello smoke" || { echo "FAIL greet"; exit 1; }
"$PY" -m {{ package_name }} count "a b c" | grep -q "words=3" || { echo "FAIL count"; exit 1; }

echo "smoke: all checks passed"