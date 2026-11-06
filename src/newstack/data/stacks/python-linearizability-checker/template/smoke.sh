#!/usr/bin/env bash
# End-to-end checks against the packaged command, not against the modules.
#
# Run it with the project's interpreter:
#   PY=.venv/bin/python bash smoke.sh
set -uo pipefail

PY="${PY:-python3}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

PASS=0
FAILS=0

ok() {
    PASS=$((PASS + 1))
    printf 'ok   %s\n' "$1"
}

bad() {
    FAILS=$((FAILS + 1))
    printf 'FAIL %s\n' "$1"
}

check_equal() {
    if [ "$2" = "$3" ]; then
        ok "$1"
    else
        bad "$1 (expected '$2', got '$3')"
    fi
}

check_contains() {
    case "$3" in
        *"$2"*) ok "$1" ;;
        *) bad "$1 (missing '$2' in: ${3:0:160})" ;;
    esac
}

run() {
    OUT="$("$@" 2>&1)"
    STATUS=$?
}

FIXTURES="$(cd "$(dirname "$0")" && pwd)/fixtures"

# --- the command answers at all ---------------------------------------------
run "$PY" -m "$MODULE" --version
check_equal "version exits zero" 0 "$STATUS"
check_contains "version names the program" "$PROGRAM" "$OUT"

run "$PY" -m "$MODULE" --help
check_equal "help exits zero" 0 "$STATUS"
check_contains "help lists check" "check" "$OUT"
check_contains "help lists compare" "compare" "$OUT"

# --- a history that is linearizable -----------------------------------------
run "$PY" -m "$MODULE" check --history "$FIXTURES/sequential.jsonl"
check_equal "a linearizable history exits zero" 0 "$STATUS"
check_contains "the verdict is printed" "verdict    linearizable" "$OUT"
check_contains "a witness is printed" "witness    one order that holds:" "$OUT"
check_contains "the search is counted" "search     " "$OUT"

# --- a history that is not --------------------------------------------------
run "$PY" -m "$MODULE" check --history "$FIXTURES/stale-read.jsonl"
check_equal "a refused history exits one" 1 "$STATUS"
check_contains "the verdict says so" "not linearizable" "$OUT"
check_contains "a core is printed" "core       " "$OUT"
check_contains "the core is minimal" "removing any one" "$OUT"

# --- the write may land between two reads -----------------------------------
run "$PY" -m "$MODULE" check --history "$FIXTURES/straddle.jsonl"
check_equal "the straddle history exits zero" 0 "$STATUS"
check_contains "the witness puts the write in the middle" "client 0 write 1" "$OUT"

# --- json -------------------------------------------------------------------
run "$PY" -m "$MODULE" check --history "$FIXTURES/sequential.jsonl" --json
check_equal "json exits zero" 0 "$STATUS"
run "$PY" -c "import json,sys; d=json.loads(sys.argv[1]); print(d['linearizable'], d['order'])" "$OUT"
check_equal "the payload carries the order" "True [0, 1, 2]" "$OUT"

# --- the initial value can be given -----------------------------------------
printf '%s\n' '{"client": 0, "op": "read", "value": 7, "start": 0, "end": 1}' > "$WORK/read-seven.jsonl"
run "$PY" -m "$MODULE" check --history "$WORK/read-seven.jsonl"
check_equal "reading 7 from a register that starts at 0 is refused" 1 "$STATUS"
run "$PY" -m "$MODULE" check --history "$WORK/read-seven.jsonl" --initial 7
check_equal "and accepted when the register starts at 7" 0 "$STATUS"

# --- refusals ---------------------------------------------------------------
run "$PY" -m "$MODULE" check --history "$WORK/nope.jsonl"
check_equal "a missing file is unusable" 2 "$STATUS"
check_contains "the error names the file" "nope.jsonl" "$OUT"

printf '%s\n' '{"client": 0, "op": "read"' > "$WORK/broken.jsonl"
run "$PY" -m "$MODULE" check --history "$WORK/broken.jsonl"
check_equal "a broken line is unusable" 2 "$STATUS"
check_contains "the error says it is not JSON" "not JSON" "$OUT"

printf '%s\n' '{"client": 0, "op": "read", "value": 1, "start": 3, "end": 1}' > "$WORK/impossible.jsonl"
run "$PY" -m "$MODULE" check --history "$WORK/impossible.jsonl"
check_equal "a response before its invocation is unusable" 2 "$STATUS"
check_contains "the error names the times" "before the invocation" "$OUT"

# --- shrink -----------------------------------------------------------------
run "$PY" -m "$MODULE" shrink --history "$FIXTURES/stale-read.jsonl"
check_equal "shrink exits one on a refused history" 1 "$STATUS"
check_contains "shrink prints the core size" "of 2 operation(s)" "$OUT"

run "$PY" -m "$MODULE" shrink --history "$FIXTURES/sequential.jsonl"
check_equal "shrink exits zero on a good history" 0 "$STATUS"
check_contains "and says there is nothing to do" "nothing to shrink" "$OUT"

# --- compare ----------------------------------------------------------------
run "$PY" -m "$MODULE" compare --history "$FIXTURES/straddle.jsonl"
check_equal "compare exits zero when the checkers agree" 0 "$STATUS"
check_contains "compare reports agreement" "the two checkers agree" "$OUT"
check_contains "compare counts the yardstick" "order(s) tried" "$OUT"

"$PY" - <<'PY' > "$WORK/big.jsonl"
import json
for i in range(9):
    print(json.dumps({"client": 0, "op": "read", "value": 0, "start": i, "end": i + 1}))
PY
run "$PY" -m "$MODULE" compare --history "$WORK/big.jsonl"
check_equal "compare refuses a history it cannot enumerate" 2 "$STATUS"
check_contains "and says where it stops" "stops at 8" "$OUT"

# --- demo and selftest ------------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "demo exits zero" 0 "$STATUS"
check_contains "demo holds every story" "stories      6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "selftest exits zero" 0 "$STATUS"
check_contains "selftest reports no failures" "0 failed" "$OUT"

printf '\nsmoke: %d passed, %d failed\n' "$PASS" "$FAILS"
[ "$FAILS" -eq 0 ]
