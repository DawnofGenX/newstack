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

# --- building a tree ------------------------------------------------------------
run "$PY" -m "$MODULE" build --count 32
check_equal "the build exits zero" 0 "$STATUS"
check_contains "the build names the size" "size 32" "$OUT"
check_contains "the build states the walk-limit" "walk-limit 6" "$OUT"

run "$PY" -m "$MODULE" build --values fixtures/values.txt
check_equal "the codex builds" 0 "$STATUS"
check_contains "the codex is twenty-four values" "size 24" "$OUT"
check_contains "the cell invariant holds" "invariant True" "$OUT"

# --- prefix answers the running list-sum ------------------------------------------
run "$PY" -m "$MODULE" sum --values fixtures/values.txt 5
check_equal "a prefix exits zero" 0 "$STATUS"
check_contains "the prefix is the running sum" "answer 16" "$OUT"
check_contains "the walk counted its cells" "cells 2" "$OUT"

run "$PY" -m "$MODULE" sum --values fixtures/values.txt 24
check_contains "the total is the whole corpus" "answer 493" "$OUT"

run "$PY" -m "$MODULE" sum --values fixtures/values.txt 99
check_equal "a count past the tree exits two" 2 "$STATUS"

# --- an add shifts the cells --------------------------------------------------------
run "$PY" -m "$MODULE" add --values fixtures/values.txt 2 7
check_equal "an add exits zero" 0 "$STATUS"
check_contains "the add names the new value" "answer 10" "$OUT"
check_contains "the climb counted its cells" "cells 4" "$OUT"

run "$PY" -m "$MODULE" add --values fixtures/values.txt 30 7
check_equal "an index past the tree is refused" 2 "$STATUS"
check_contains "the refusal names the seat" "is no seat" "$OUT"

# --- a range is two prefixes -----------------------------------------------------------
run "$PY" -m "$MODULE" range --values fixtures/values.txt 2 6
check_equal "a window exits zero" 0 "$STATUS"
check_contains "the window is the slice" "answer 19" "$OUT"

run "$PY" -m "$MODULE" range --values fixtures/values.txt 6 2
check_equal "an inverted window is refused" 2 "$STATUS"
check_contains "the window is named" "unusable" "$OUT"

# --- the fixture stream -------------------------------------------------------------------
FIXTURE_STREAM=fixtures/values.txt
COUNT=$(grep -cv '^\s*\(#\|$\)' "$FIXTURE_STREAM")
if [[ "$COUNT" -ge 20 ]]; then
  ok "the fixture holds a corpus ($COUNT values)"
else
  bad "the fixture is too small ($COUNT values)"
fi

# --- the stories and the invariants ------------------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
