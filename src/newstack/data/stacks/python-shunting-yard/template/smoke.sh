#!/usr/bin/env bash
# The smoke test runs the tool the way a user would and checks what it says.
# PY points at the interpreter that has this package installed.
set -uo pipefail

PY="${PY:-python3}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

check_contains() {
  local name="$1" needle="$2" text="$3"
  if [[ "$text" == *"$needle"* ]]; then
    ok "$name"
  else
    bad "$name"
    printf '       wanted %q in %q\n' "$needle" "${text:0:200}"
  fi
}

check_equal() {
  local name="$1" want="$2" got="$3"
  if [[ "$want" == "$got" ]]; then
    ok "$name"
  else
    bad "$name"
    printf '       wanted %q, got %q\n' "$want" "$got"
  fi
}

run() {
  OUT=$("$@" 2>&1)
  STATUS=$?
}

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

echo "smoke: $PROGRAM"

run "$PY" -m "$MODULE" --version
check_equal "the version exits zero" 0 "$STATUS"
check_contains "the banner carries the version" "0.1.0" "$OUT"

run "$PY" -m "$MODULE" --help
check_equal "help exits zero" 0 "$STATUS"
check_contains "help lists the subcommands" "selftest" "$OUT"

# --- the yard, the oracle, and the answer ------------------------------------------
run "$PY" -m "$MODULE" eval "3 + 4 * 2 / ( 1 - 5 ) * 2"
check_equal "an eval exits zero" 0 "$STATUS"
check_contains "the answer is the documented one" "value      -1" "$OUT"

run "$PY" -m "$MODULE" eval "2 + 3 * 4" --json
check_equal "a json eval exits zero" 0 "$STATUS"
VALUE=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["value"])' "$OUT")
check_equal "the json answer is fourteen" "14" "$VALUE"

run "$PY" -m "$MODULE" postfix "2 + 3 * 4"
check_equal "a postfix exits zero" 0 "$STATUS"
check_contains "the queue is postfix" "2 3 4 * +" "$OUT"

run "$PY" -m "$MODULE" eval "7 / 2"
check_equal "a division exits zero" 0 "$STATUS"
check_contains "a division floors" "value      3" "$OUT"

# --- the edges the gate refuses ------------------------------------------------------
run "$PY" -m "$MODULE" eval "( 1 + 2"
check_equal "an unclosed paren exits two" 2 "$STATUS"
check_contains "the parenthesis is named" "unbalanced" "$OUT"

run "$PY" -m "$MODULE" eval "5 / 0"
check_equal "a divided zero exits two" 2 "$STATUS"

run "$PY" -m "$MODULE" eval "2 ** 3"
check_equal "a power is no operator" 2 "$STATUS"

run "$PY" -m "$MODULE" report --corpus "$WORK/missing.txt"
check_equal "a missing ledger exits two" 2 "$STATUS"

# --- the fixture ledger, record after record ------------------------------------------
COUNT=$(grep -cvE '^[[:space:]]*(#|$)' fixtures/records.txt)
if [[ "$COUNT" -ge 8 ]]; then
  ok "the fixture holds a ledger ($COUNT records)"
else
  bad "the fixture is too small ($COUNT records)"
fi

BROKE=$("$PY" - <<'PYEOF'
from {{ package_name }}.calc import evaluate, value_of
from {{ package_name }}.corpus import audit, load_records
from {{ package_name }}.oracle import descent
from {{ package_name }}.yard import postfix_text, to_postfix

broken = []
for record in load_records("fixtures/records.txt"):
    if audit(record) or postfix_text(to_postfix(record.expr)) != record.postfix:
        broken.append(record.expr)
    if evaluate(to_postfix(record.expr)) != value_of(record.expr) or \
            descent(record.expr) != value_of(record.expr):
        broken.append(record.expr)
print(len(broken))
PYEOF
)
check_equal "every fixture record audits silent, all three ways" 0 "$BROKE"

# --- the stories and the invariants -------------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
