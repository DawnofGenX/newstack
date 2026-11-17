#!/usr/bin/env bash
set -euo pipefail
.venv/bin/python -m pytest
.venv/bin/python -m {{ package_name }} --selftest
echo "smoke: PASS"