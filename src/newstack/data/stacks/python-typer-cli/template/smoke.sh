#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
PY="$ROOT/.venv/bin/python"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
store="$work/tasks.json"

"$PY" -m {{ package_name }} add "buy milk" --file "$store" | grep -q "added 1" || { echo "FAIL add"; exit 1; }
"$PY" -m {{ package_name }} list --file "$store" | grep -q "buy milk" || { echo "FAIL list"; exit 1; }
"$PY" -m {{ package_name }} done 1 --file "$store" | grep -q "done 1" || { echo "FAIL done"; exit 1; }
"$PY" -m {{ package_name }} rm 1 --file "$store" | grep -q "removed 1" || { echo "FAIL rm"; exit 1; }

echo "smoke: all checks passed"
