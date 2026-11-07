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

# --- add seats, check asks, the promise holds ---------------------------------------
run "$PY" -m "$MODULE" add --key 7 --key 42
check_equal "an add exits zero" 0 "$STATUS"
check_contains "the keys are echoed" "added      7 42" "$OUT"
check_contains "the audit names no break" "audit      0 breaks" "$OUT"

run "$PY" -m "$MODULE" check 165
check_equal "a seeded key checks present" 0 "$STATUS"
check_contains "the answer says present" "present" "$OUT"

run "$PY" -m "$MODULE" check 1
check_equal "an unseen key checks absent" 1 "$STATUS"
check_contains "the answer says absent" "absent" "$OUT"

run "$PY" -m "$MODULE" check 132 --seed 13
check_equal "seed 13 checks 132 present" 0 "$STATUS"

# --- the shipped audit, counted -------------------------------------------------------
run "$PY" -m "$MODULE" report
check_equal "the report exits zero" 0 "$STATUS"
check_contains "the re-asks are booked" "7920 booked, 7920 run" "$OUT"
check_contains "no key read absent" "false neg  0" "$OUT"
check_contains "no absent key lied" "false pos  0" "$OUT"
check_contains "the audit broke on nothing" "breaks     0" "$OUT"

REPORT=$("$PY" -m "$MODULE" report --json)
FNS=$("$PY" -c 'import json,sys; print(sum(len(v["false_negatives"]) for v in json.loads(sys.argv[1])["verdicts"]))' "$REPORT")
FPS=$("$PY" -c 'import json,sys; print(sum(len(v["false_positives"]) for v in json.loads(sys.argv[1])["verdicts"]))' "$REPORT")
check_equal "the json ledger holds no false negatives" 0 "$FNS"
check_equal "the json ledger holds no false positives" 0 "$FPS"

# --- the same seed, the same answers ---------------------------------------------------
run "$PY" -m "$MODULE" seed 7
check_equal "a seed replays" 0 "$STATUS"
check_contains "the replay is identical" "replay     identical" "$OUT"
check_contains "the first key is 165" "first keys 165" "$OUT"

# --- the gates refuse what is not a key -------------------------------------------------
run "$PY" -m "$MODULE" check x
check_equal "a text key is unusable" 2 "$STATUS"
check_contains "the text is named" "not a decimal integer" "$OUT"

run "$PY" -m "$MODULE" check 256
check_equal "256 leaves the universe" 2 "$STATUS"

run "$PY" -m "$MODULE" check 7 --width 7
check_equal "a narrow array is refused" 2 "$STATUS"

# --- the frozen streams replay the arithmetic --------------------------------------------
LINES=$(grep -cvE '^[[:space:]]*(#|$)' fixtures/streams.txt)
if [[ "$LINES" -ge 5 ]]; then
  ok "the fixture freezes five streams ($LINES lines)"
else
  bad "the fixture is too small ($LINES lines)"
fi

BROKE=$("$PY" - <<'PYEOF'
from {{ package_name }}.stream import load_fixture, stream
from {{ package_name }}.bloom import Bloom

broken = 0
for plan in load_fixture("fixtures/streams.txt"):
    if plan.keys != stream(plan.seed):
        broken += 1
    filter_ = Bloom(1024, 4, plan.seed)
    for key in plan.keys:
        filter_.add(key)
    broken += len(filter_.audit())
print(broken)
PYEOF
)
check_equal "every fixture stream replays and seats clean" 0 "$BROKE"

# --- the stories and the invariants --------------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
