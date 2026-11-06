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
check_equal "the version names the program" 0 "$STATUS"
check_contains "the banner carries the version" "0.1.0" "$OUT"

run "$PY" -m "$MODULE" --help
check_equal "help exits zero" 0 "$STATUS"
check_contains "help lists the subcommands" "selftest" "$OUT"

# --- building a map -----------------------------------------------------------
run "$PY" -m "$MODULE" build --count 32
check_equal "the build exits zero" 0 "$STATUS"
check_contains "the build names the size" "size 32" "$OUT"
check_contains "the build counts its flips" "coin flip" "$OUT"

run "$PY" -m "$MODULE" build --count 1
check_equal "a single key still builds" 0 "$STATUS"
check_contains "one key is one key" "size 1 height" "$OUT"

# --- rank and select ----------------------------------------------------------
run "$PY" -m "$MODULE" rank --pairs fixtures/pairs.txt 30
check_equal "rank exits zero" 0 "$STATUS"
check_contains "thirteen keys sit below thirty" "rank 17" "$OUT"

run "$PY" -m "$MODULE" rank --pairs fixtures/pairs.txt 0
check_contains "an absent key still gets a rank" "rank 11" "$OUT"

run "$PY" -m "$MODULE" select --pairs fixtures/pairs.txt 0
check_equal "select exits zero" 0 "$STATUS"
check_contains "the first position holds the smallest key" "'-97' = 0" "$OUT"

run "$PY" -m "$MODULE" select --pairs fixtures/pairs.txt 44
check_contains "the last position is inside the map" "'171' = 44" "$OUT"

run "$PY" -m "$MODULE" select --pairs fixtures/pairs.txt 99
check_equal "a position past the map exits one" 1 "$STATUS"
check_contains "an empty position is admitted" "holds nothing" "$OUT"

# --- pair streams ---------------------------------------------------------------
PAIRS="$WORK/pairs.txt"
printf '7 70\n8 80\n9 90\n' >"$PAIRS"
run "$PY" -m "$MODULE" rank --pairs "$PAIRS" 8
check_contains "a written stream reads back" "rank 1" "$OUT"

run "$PY" -m "$MODULE" build --pairs "$WORK/missing.txt"
check_equal "a missing stream is unusable" 2 "$STATUS"
check_contains "the file is named" "cannot read" "$OUT"

NOISE="$WORK/noise.txt"
printf 'one two\n' >"$NOISE"
run "$PY" -m "$MODULE" build --pairs "$NOISE"
check_equal "a stream of noise is unusable" 2 "$STATUS"
check_contains "the noise is named" "non-integer" "$OUT"

# --- the fixture stream ----------------------------------------------------------
COUNT=0
while IFS= read -r line; do
  [[ -z "$line" || "$line" == \#* ]] && continue
  COUNT=$((COUNT + 1))
done <fixtures/pairs.txt
if [[ "$COUNT" -ge 20 ]]; then ok "the fixture holds a stream ($COUNT pairs)"; else bad "the fixture is too small ($COUNT pairs)"; fi

# --- the stories and the invariants -----------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
