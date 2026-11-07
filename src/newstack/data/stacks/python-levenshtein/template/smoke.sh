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

# --- distances, the row walk answering -------------------------------------------
run "$PY" -m "$MODULE" distance cat cat
check_equal "a distance exits zero" 0 "$STATUS"
check_contains "an identical pair costs nothing" "distance   0" "$OUT"

run "$PY" -m "$MODULE" distance cart cat
check_equal "a change exits zero" 0 "$STATUS"
check_contains "one letter is one change" "distance   1" "$OUT"

run "$PY" -m "$MODULE" distance knight light --json
SPENT=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["distance"])' "$OUT")
check_equal "knight to light is two changes" 2 "$SPENT"

run "$PY" -m "$MODULE" distance cat ""
check_equal "to nothing exits zero" 0 "$STATUS"
check_contains "to nothing is a change per letter" "distance   3" "$OUT"

# --- nearest, the scan's argmin with the tie rule -----------------------------------
run "$PY" -m "$MODULE" nearest --words fixtures/words.txt crt
check_equal "a nearest exits nonzero without an exact word" 1 "$STATUS"
check_contains "the nearest is the tied head" "nearest    'cart' at 1" "$OUT"

run "$PY" -m "$MODULE" nearest --words fixtures/words.txt cat --json
NEAR=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["nearest"])' "$OUT")
check_equal "an exact word is its own nearest" "cat" "$NEAR"

# --- the edges the gate refuses ------------------------------------------------------
run "$PY" -m "$MODULE" nearest --words "$WORK/missing.txt" cat
check_equal "a missing word list is unusable" 2 "$STATUS"
check_contains "the file is named" "no such word list" "$OUT"

run "$PY" -m "$MODULE" distance Cat cat
check_equal "uppercase is refused at the gate" 2 "$STATUS"
check_contains "the stranger is named" "is not lowercase" "$OUT"

NOISE="$WORK/noise.txt"
printf '7\n1.5\n' >"$NOISE"
run "$PY" -m "$MODULE" nearest --words "$NOISE" cat
check_equal "a noisy word list is unusable" 2 "$STATUS"
check_contains "the noise is named" "the word list holds" "$OUT"

# --- the fixture corpus ---------------------------------------------------------------
COUNT=$(grep -cvE '^[[:space:]]*(#|$)' fixtures/words.txt)
if [[ "$COUNT" -ge 12 ]]; then
  ok "the fixture holds a corpus ($COUNT words)"
else
  bad "the fixture is too small ($COUNT words)"
fi

# --- the stories and the invariants ----------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
