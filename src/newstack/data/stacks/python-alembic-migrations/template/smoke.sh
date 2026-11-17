#!/usr/bin/env bash
set -euo pipefail

rm -f app.db

.venv/bin/alembic upgrade head

fail() {
  echo " FAIL: $*" >&2
  exit 1
}

schema="$(sqlite3 app.db ".schema items")"
echo "$schema" | grep -q "CREATE TABLE items" || fail "items table missing"
echo "$schema" | grep -q "status" || fail "status column missing"

cols="$(sqlite3 app.db "PRAGMA table_info(items);")"
echo "$cols" | grep -q "status" || fail "status not in table_info"

echo "smoke ok"