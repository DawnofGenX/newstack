#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
PY="$ROOT/.venv/bin/python"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

printf 'secret smoke data\n' > "$work/plain.txt"
VAULT="$work/vault"
"$PY" -m {{ package_name }} encrypt "$work/plain.txt" --password correct --vault "$VAULT"
ENTRY=$("$PY" -m {{ package_name }} list --vault "$VAULT" | "$PY" -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")
"$PY" -m {{ package_name }} decrypt "$ENTRY" --password correct --out "$work/out.txt" --vault "$VAULT"
diff "$work/plain.txt" "$work/out.txt"

set +e
"$PY" -m {{ package_name }} decrypt "$ENTRY" --password wrong --out "$work/bad.txt" --vault "$VAULT" >/dev/null 2>&1
STATUS=$?
set -e
if [ "$STATUS" -eq 0 ]; then echo "FAIL wrong password accepted"; exit 1; fi

echo "smoke: all checks passed"
