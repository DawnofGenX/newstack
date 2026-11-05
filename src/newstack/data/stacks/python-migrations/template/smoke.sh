#!/usr/bin/env bash
# Smoke: a real database file, a real ledger, and the three refusals.
set -euo pipefail
cd "$(dirname "$0")"

if [ -z "${PY:-}" ]; then
  if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=python3; fi
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

DB="$TMP/app.db"
cli() { "$PY" -m {{ package_name }} "$1" --db "$DB" --dir "${2:-migrations}"; }
say() { echo "ok $1"; }

# 1. a fresh database applies every migration, in order
cli up >"$TMP/up.txt"
grep -q '^applied 0001_create_notes ' "$TMP/up.txt"
grep -q '^applied 0003_notes_by_title ' "$TMP/up.txt"
grep -q '^applied 3 migrations (0 already present)$' "$TMP/up.txt"
say "a fresh database applied the three shipped migrations"

# 2. the ledger is in the database, so it survives the process
"$PY" - "$DB" <<'PY'
import sqlite3, sys
rows = sqlite3.connect(sys.argv[1]).execute(
    "SELECT migration_id FROM schema_migrations ORDER BY migration_id"
).fetchall()
assert [row[0] for row in rows] == ["0001", "0002", "0003"], rows
PY
say "the ledger rows are in the database file"

# 3. running again changes nothing
cli up >"$TMP/again.txt"
grep -q '^applied 0 migrations (3 already present)$' "$TMP/again.txt"
say "a second run applied nothing"

# 4. verify agrees
cli verify | grep -q '^ok 3 migrations match the ledger$'
say "verify agrees with the ledger"

# 5. an edited applied file is drift: exit 1, and nothing new runs
cp -r migrations "$TMP/edited"
printf -- '-- reworded after it ran\n' >>"$TMP/edited/0002_add_pinned.sql"
printf 'ALTER TABLE notes ADD COLUMN later INTEGER;\n' >"$TMP/edited/0004_later.sql"
set +e
cli up "$TMP/edited" >"$TMP/drift.out" 2>"$TMP/drift.err"
status=$?
set -e
test "$status" -eq 1
grep -q 'modified after being applied: 0002_add_pinned' "$TMP/drift.err"
say "an edited applied file exits 1 and blocks the pending one"

# 6. a duplicate number is unusable, not drift
cp -r migrations "$TMP/dup"
printf 'SELECT 1;\n' >"$TMP/dup/0002_again.sql"
set +e
cli status "$TMP/dup" >/dev/null 2>"$TMP/dup.err"
status=$?
set -e
test "$status" -eq 2
grep -q '0002 is claimed twice' "$TMP/dup.err"
say "a duplicate migration number exits 2"

# 7. a failing file rolls back its own statements, and says so
cp -r migrations "$TMP/broken"
printf 'CREATE TABLE debris (x INTEGER);\nINSERT INTO nope VALUES (1);\n' >"$TMP/broken/0004_broken.sql"
set +e
cli up "$TMP/broken" >/dev/null 2>"$TMP/broken.err"
status=$?
set -e
test "$status" -eq 2
grep -q 'nothing from this file was applied' "$TMP/broken.err"
"$PY" - "$DB" <<'PY'
import sqlite3, sys
rows = sqlite3.connect(sys.argv[1]).execute(
    "SELECT count(*) FROM sqlite_master WHERE name = 'debris'"
).fetchone()
assert rows[0] == 0, "the CREATE TABLE survived the rollback"
PY
say "a failing migration rolls back and leaves no table"

echo "smoke: all checks passed"
