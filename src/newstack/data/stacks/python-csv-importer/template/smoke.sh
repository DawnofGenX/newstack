#!/bin/sh
set -eu

echo "smoke: python-csv-importer"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

if ! .venv/bin/python -m pytest >"$work/tests.log" 2>&1; then
  cat "$work/tests.log"
  exit 1
fi
echo "  ok   tests pass"

cat >"$work/data.csv" <<'EOF'
id,name,qty
1,alpha,2
2,beta,3
EOF

.venv/bin/python -m {{ package_name }} "$work/data.csv" "$work/out.db" --dry-run >"$work/dry.log" 2>&1
if [ -f "$work/out.db" ]; then echo "dry-run created db"; cat "$work/dry.log"; exit 1; fi
echo "  ok   dry-run writes nothing"

.venv/bin/python -m {{ package_name }} "$work/data.csv" "$work/out.db" >"$work/run.log" 2>&1
.venv/bin/python -m {{ package_name }} "$work/data.csv" "$work/out.db" >"$work/run2.log" 2>&1
count=$(.venv/bin/python -c "import sqlite3,sys; print(sqlite3.connect('$work/out.db').execute('SELECT COUNT(*) FROM records').fetchone()[0])")
if [ "$count" != "2" ]; then echo "expected 2 rows, got $count"; cat "$work/run.log" "$work/run2.log"; exit 1; fi
echo "  ok   idempotent re-run"

echo "smoke: PASS"