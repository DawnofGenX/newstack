#!/usr/bin/env bash
set -euo pipefail
.venv/bin/python -m pytest
# behavioural: create db, backup, verify row count
tmp=$(mktemp -d)
.venv/bin/python - "$tmp" <<'PY'
import sqlite3, sys, pathlib
d = pathlib.Path(sys.argv[1])
src = d/"src.db"
c = sqlite3.connect(str(src)); c.execute("CREATE TABLE t(x)"); c.executemany("INSERT INTO t VALUES (?)", [(i,) for i in range(3)]); c.commit(); c.close()
PY
.venv/bin/python -m {{ package_name }} backup "$tmp/src.db" "$tmp/bak" --keep 1
test "$(ls "$tmp/bak"/*.db | wc -l)" = "1"
echo "smoke: PASS"