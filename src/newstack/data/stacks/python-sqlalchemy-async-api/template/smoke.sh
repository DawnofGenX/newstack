#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
"$ROOT/.venv/bin/python" -m {{ package_name }} --selftest | grep -q "selftest: ok" || { echo "FAIL selftest"; exit 1; }

echo "smoke: all checks passed"