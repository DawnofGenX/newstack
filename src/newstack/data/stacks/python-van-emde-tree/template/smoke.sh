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

# --- seating keys, the walk equal to the sort ----------------------------------------
run "$PY" -m "$MODULE" add --keys fixtures/keys.txt 77
check_equal "an add exits zero" 0 "$STATUS"
check_contains "the add grew the tree" "seats      17" "$OUT"

run "$PY" -m "$MODULE" add --keys fixtures/keys.txt 3
check_equal "a double add exits zero" 0 "$STATUS"
check_contains "a double add sat once" "seats      16" "$OUT"

run "$PY" -m "$MODULE" remove --keys fixtures/keys.txt 3
check_equal "a remove exits zero" 0 "$STATUS"
check_contains "the remove shrank the tree" "seats      15" "$OUT"

run "$PY" -m "$MODULE" remove --keys fixtures/keys.txt 254
check_equal "an absent remove exits two" 2 "$STATUS"
check_contains "the absence is named" "no key 254" "$OUT"

# --- the seeks the tree owes the scan --------------------------------------------------
run "$PY" -m "$MODULE" succ --keys fixtures/keys.txt 100
check_equal "a seek exits zero" 0 "$STATUS"
check_contains "the successor is the scan" "successor  111" "$OUT"

run "$PY" -m "$MODULE" pred --keys fixtures/keys.txt 100
check_equal "a reverse seek exits zero" 0 "$STATUS"
check_contains "the predecessor is the scan" "predecessor 99" "$OUT"

run "$PY" -m "$MODULE" succ --keys fixtures/keys.txt 255
check_equal "the last seat succeeds itself" 0 "$STATUS"
check_contains "the last seat answers" "successor  255" "$OUT"

run "$PY" -m "$MODULE" has --keys fixtures/keys.txt 99
check_equal "a seated key exits zero" 0 "$STATUS"
check_contains "the seat is admitted" "seated     True" "$OUT"

run "$PY" -m "$MODULE" has --keys fixtures/keys.txt 100
check_equal "an absent key exits one" 1 "$STATUS"
check_contains "the nothing is named" "seated     False" "$OUT"

WANT=$(printf '0 3 7 17 31 42 61 88 99 111 120 150 176 200 233 255')
run "$PY" -m "$MODULE" min --keys fixtures/keys.txt
check_equal "the min exits zero" 0 "$STATUS"
check_contains "the min is the first seat" "min        0" "$OUT"
run "$PY" -m "$MODULE" max --keys fixtures/keys.txt --json
MAX=$(printf '%s' "$OUT" | "$PY" -c 'import json,sys; print(json.loads(sys.stdin.read())["max"])')
check_equal "the max is the last seat" "255" "$MAX"
run "$PY" -m "$MODULE" succ --keys fixtures/keys.txt 0 --json
LIVE=$(printf '%s' "$OUT" | "$PY" -c 'import json,sys; print(" ".join(map(str, json.loads(sys.stdin.read())["live"])))')
check_equal "the walk is the scan" "$WANT" "$LIVE"

# --- the edges the gate refuses --------------------------------------------------------
run "$PY" -m "$MODULE" min --keys "$WORK/missing.txt"
check_equal "a missing key list is unusable" 2 "$STATUS"
check_contains "the file is named" "no such key list" "$OUT"

NOISE="$WORK/noise.txt"
printf '7\n1.5\n' >"$NOISE"
run "$PY" -m "$MODULE" min --keys "$NOISE"
check_equal "a noisy key list is unusable" 2 "$STATUS"
check_contains "the noise is named" "not a seat" "$OUT"

OUT_OF_RANGE="$WORK/range.txt"
printf '7\n999\n' >"$OUT_OF_RANGE"
run "$PY" -m "$MODULE" min --keys "$OUT_OF_RANGE"
check_equal "a seat past the universe is unusable" 2 "$STATUS"
check_contains "the universe is named" "not a seat" "$OUT"

# --- the fixture corpus -----------------------------------------------------------------
COUNT=$(grep -cvE '^[[:space:]]*(#|$)' fixtures/keys.txt)
if [[ "$COUNT" -ge 12 ]]; then
  ok "the fixture holds a corpus ($COUNT seats)"
else
  bad "the fixture is too small ($COUNT seats)"
fi

# --- the stories and the invariants ------------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
