#!/usr/bin/env bash
set -euo pipefail

rm -f jobs.db

.venv/bin/python -m {{ package_name }} --ticks 5

fail() {
  echo " FAIL: $*" >&2
  exit 1
}

count="$(sqlite3 jobs.db "SELECT COUNT(*) FROM job_runs;")"
[[ "$count" == "5" ]] || fail "expected 5 rows got $count"

echo "smoke ok"