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

# --- counting the fixture, key by key -------------------------------------------
run "$PY" -m "$MODULE" count --stream fixtures/stream.txt 7
check_equal "a counted key exits zero" 0 "$STATUS"
check_contains "the count is the ledger sum" "count      1" "$OUT"
check_contains "the key is tracked" "tracked    True" "$OUT"

run "$PY" -m "$MODULE" count --stream fixtures/stream.txt 199
check_equal "a second key exits zero" 0 "$STATUS"
check_contains "the count is the ledger sum" "count      3" "$OUT"

run "$PY" -m "$MODULE" count --stream fixtures/stream.txt 1
check_equal "an absent key exits one" 1 "$STATUS"
check_contains "the absence is admitted" "tracked    False" "$OUT"
check_contains "the nothing counts zero" "count      0" "$OUT"

run "$PY" -m "$MODULE" add --stream fixtures/stream.txt 7 2
check_equal "an add exits zero" 0 "$STATUS"
check_contains "the add grew the count" "count      3" "$OUT"
check_contains "the add grew the ledger" "total      38" "$OUT"

run "$PY" -m "$MODULE" report --stream fixtures/stream.txt
check_equal "a report exits zero" 0 "$STATUS"
check_contains "the grid is named" "width      256" "$OUT"
check_contains "the rows are named" "rows       37,71,109,151,199" "$OUT"
check_contains "the shipped grid drifts nowhere" "drift      0" "$OUT"

# --- the deterministic stream -----------------------------------------------------
FIRST=$("$PY" -m "$MODULE" seed --count 8 --seed 7 | tr '\n' ';')
SECOND=$("$PY" -m "$MODULE" seed --count 8 --seed 7 | tr '\n' ';')
check_equal "the same seed replays itself" "$FIRST" "$SECOND"

printf '%s\n' "7 2" >"$WORK/tiny.txt"
run "$PY" -m "$MODULE" count --stream "$WORK/tiny.txt" 7
check_equal "a written stream counts" 0 "$STATUS"
check_contains "the tiny count is the sum" "count      2" "$OUT"

# --- the edges the gate refuses ----------------------------------------------------
run "$PY" -m "$MODULE" count --stream "$WORK/missing.txt" 7
check_equal "a missing stream is unusable" 2 "$STATUS"
check_contains "the file is named" "no such stream" "$OUT"

NOISE="$WORK/noise.txt"
printf '7\n1.5\n' >"$WORK/noise.txt"
run "$PY" -m "$MODULE" count --stream "$NOISE" 7
check_equal "a noisy stream is unusable" 2 "$STATUS"
check_contains "the noise is named" "not 'key n'" "$OUT"

run "$PY" -m "$MODULE" count --stream fixtures/stream.txt 300
check_equal "an off-universe key is unusable" 2 "$STATUS"
check_contains "the universe is named" "off [0, 256)" "$OUT"

# --- the fixture corpus -------------------------------------------------------------
COUNT=$(grep -cvE '^[[:space:]]*(#|$)' fixtures/stream.txt)
if [[ "$COUNT" -ge 12 ]]; then
  ok "the fixture holds a corpus ($COUNT events)"
else
  bad "the fixture is too small ($COUNT events)"
fi

# --- the stories and the invariants --------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
