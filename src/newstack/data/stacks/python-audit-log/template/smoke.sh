#!/usr/bin/env bash
# End-to-end checks: append, read, tamper, detect. No server, no port.
set -uo pipefail

PY="${PY:-.venv/bin/python}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

DB="$WORK/audit.db"
HEAD="$WORK/head.json"

passed=0
failed=0

ok() {
    passed=$((passed + 1))
    printf 'ok    %s\n' "$1"
}

bad() {
    failed=$((failed + 1))
    printf 'FAIL  %s\n' "$1"
    shift
    for line in "$@"; do
        printf '      %s\n' "$line"
    done
}

check() {
    # check NAME COMMAND...: expect exit 0
    local name="$1"
    shift
    if "$@" >"$WORK/out" 2>"$WORK/err"; then
        ok "$name"
    else
        bad "$name" "exit $* " "$(cat "$WORK/out" "$WORK/err")"
    fi
}

check_contains() {
    # check_contains NAME FILE REGEX
    local name="$1"
    local file="$2"
    local pattern="$3"
    if grep -Eq "$pattern" "$file"; then
        ok "$name"
    else
        bad "$name" "wanted /$pattern/ in $file" "$(cat "$file")"
    fi
}

expect() {
    # expect NAME WANT_STATUS COMMAND...: expect an exact exit status
    local name="$1"
    local want="$2"
    shift 2
    "$@" >"$WORK/out" 2>"$WORK/err"
    local status=$?
    if [ "$status" -eq "$want" ]; then
        ok "$name"
    else
        bad "$name" "wanted exit $want, got $status: $*" "$(cat "$WORK/out" "$WORK/err")"
    fi
}

# --- the program answers for itself -----------------------------------------
check_contains "the version banner names the program" <("$PY" -m "$MODULE" --version) "^$PROGRAM [0-9]"

check "the selftest passes" "$PY" -m "$MODULE" selftest
check_contains "the selftest counted its checks" "$WORK/out" "0 failed"

# --- append ----------------------------------------------------------------
append() {
    "$PY" -m "$MODULE" --db "$DB" append "$@"
}

check "an event is appended" append --actor alice --action note.update --target note/1
check_contains "the append prints the sequence and the hash" "$WORK/out" "^seq 1 +hash [0-9a-f]{64}$"

append --actor bob --action note.delete --target note/2 >/dev/null
append --actor alice --action login --target alice --detail-json '{"ip": "10.0.0.7"}' >/dev/null

check_contains "list shows every event" <("$PY" -m "$MODULE" --db "$DB" list) "^ *3 +[0-9-]{10}[T ]"
check_contains "list counts the log" <("$PY" -m "$MODULE" --db "$DB" list) "3 event\(s\) listed; 3 in the log"

# --- an honest log verifies ------------------------------------------------
check "a clean log verifies" "$PY" -m "$MODULE" --db "$DB" verify
check_contains "verify says what it recomputed" "$WORK/out" "^verify +ok: 3 event\(s\)"

# --- tampering with the body is caught ------------------------------------
"$PY" - "$DB" <<'PYTHON'
import sqlite3, sys
connection = sqlite3.connect(sys.argv[1])
connection.execute("UPDATE events SET body = replace(body, 'alice', 'mallory') WHERE seq = 1")
connection.commit()
connection.close()
PYTHON

expect "an edited body fails the verify" 1 "$PY" -m "$MODULE" --db "$DB" verify
check_contains "the failure names the row" "$WORK/out" "seq +1 +body-changed"
check_contains "the failure says what changed" "$WORK/out" "hashes to [0-9a-f]{8}"

# --- the checkpoint catches what the chain cannot --------------------------
"$PY" - "$WORK" <<'PYTHON'
import sqlite3, sys
from pathlib import Path
work = Path(sys.argv[1])
path = work / "honest.db"
from {{ package_name }} import store
log = store.Store(path)
for index in range(1, 4):
    log.append(actor="alice", action="note.update", target=f"note/{index}")
log.close()
PYTHON

HONEST="$WORK/honest.db"
check "a checkpoint is written" "$PY" -m "$MODULE" --db "$HONEST" checkpoint --out "$HEAD"
check_contains "the checkpoint names the head" "$WORK/out" "^checkpoint +seq 3 +count 3"
check "the checkpoint file exists" test -s "$HEAD"

"$PY" - "$HONEST" <<'PYTHON'
import sys
from pathlib import Path
from {{ package_name }} import demo, store
log = store.Store(Path(sys.argv[1]))
demo.rebuild_chain(log)
log.close()
PYTHON

check "a rebuilt chain still verifies" "$PY" -m "$MODULE" --db "$HONEST" verify
expect "the checkpoint catches the rebuild" 1 \
    "$PY" -m "$MODULE" --db "$HONEST" verify --checkpoint "$HEAD"
check_contains "the rebuild is called rewritten" "$WORK/out" "rewritten"

# --- misuse is refused, not guessed ----------------------------------------
BASE=(--db "$WORK/unused.db" append --actor alice --action x --target t)
expect "a detail without a value is refused" 2 "$PY" -m "$MODULE" "${BASE[@]}" --detail novalue
check_contains "the refusal explains the shape" "$WORK/err" "key=value"
expect "a duplicate detail is refused" 2 "$PY" -m "$MODULE" "${BASE[@]}" --detail a=1 --detail a=2
expect "a float detail is refused" 2 "$PY" -m "$MODULE" "${BASE[@]}" --detail-json '{"ratio": 0.5}'
check_contains "the float refusal explains why" "$WORK/err" "JavaScript"
expect "a missing checkpoint file is refused" 2 \
    "$PY" -m "$MODULE" --db "$DB" verify --checkpoint "$WORK/absent.json"

# --- an empty log is not a broken log --------------------------------------
check "an empty log verifies" "$PY" -m "$MODULE" --db "$WORK/fresh.db" verify
check_contains "the empty log counts zero" "$WORK/out" "ok: 0 event\(s\)"

# --- the demo shows all three attacks --------------------------------------
expect "the demo exits 1 because one attack is deliberately missed" 1 "$PY" -m "$MODULE" demo
check_contains "the demo reports four catches" "$WORK/out" "caught"
check_contains "the demo admits the miss" "$WORK/out" "MISSED"
check_contains "the demo counts its scenarios" "$WORK/out" "demo: 5 scenarios, 1 missed"

printf '\n%d passed, %d failed\n' "$passed" "$failed"
if [ "$failed" -ne 0 ]; then
    printf 'smoke: FAILED\n'
    exit 1
fi
printf 'smoke: all checks passed\n'
