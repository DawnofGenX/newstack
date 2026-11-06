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

# --- building the automaton --------------------------------------------------
PATTERNS="$WORK/patterns.txt"
printf '# the textbook set\nhe\nshe\nhis\nhers\n' >"$PATTERNS"

run "$PY" -m "$MODULE" build --patterns "$PATTERNS"
check_equal "build exits zero" 0 "$STATUS"
check_contains "the states are stated" "states" "$OUT"

run "$PY" -m "$MODULE" build --patterns "$PATTERNS" --json
SHAPES=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["patterns"])' "$OUT")
check_equal "the patterns are stated once" "['he', 'she', 'his', 'hers']" "$SHAPES"

run "$PY" -m "$MODULE" build --patterns "$WORK/missing.txt"
check_equal "a missing pattern list is unusable" 2 "$STATUS"
check_contains "the file is named" "no such pattern list" "$OUT"

# --- the sweep -----------------------------------------------------------------
TEXT="$WORK/text.txt"
printf 'ahishers' >"$TEXT"

run "$PY" -m "$MODULE" scan --patterns "$PATTERNS" --text "$TEXT"
check_equal "a hit-rich sweep exits zero" 0 "$STATUS"
check_contains "the overlap inside she surfaces" "'he' ends at 5" "$OUT"
check_contains "she surfaces whole" "'she' ends at 5" "$OUT"

run "$PY" -m "$MODULE" scan --patterns "$PATTERNS" --text "$TEXT" --json
HITS=$("$PY" -c 'import json,sys; print(len(json.loads(sys.argv[1])["hits"]))' "$OUT")
check_equal "the sweep reports four hits" "4" "$HITS"

printf 'zzzz' >"$WORK/quiet.txt"
run "$PY" -m "$MODULE" scan --patterns "$PATTERNS" --text "$WORK/quiet.txt"
check_equal "a quiet text exits one" 1 "$STATUS"

printf '' >"$WORK/nothing.txt"
run "$PY" -m "$MODULE" scan --patterns "$PATTERNS" --text "$WORK/nothing.txt"
check_equal "an empty text exits one" 1 "$STATUS"

printf '# only a comment\n' >"$WORK/hollow.txt"
run "$PY" -m "$MODULE" scan --patterns "$WORK/hollow.txt" --text "$TEXT"
check_equal "an empty pattern set is unusable as a list" 2 "$STATUS"

# --- the counter ------------------------------------------------------------------
run "$PY" -m "$MODULE" count --patterns "$PATTERNS" --text "$TEXT"
check_equal "the ledger exits zero" 0 "$STATUS"
check_contains "the sweep beats the product" "cheaper    True" "$OUT"

run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "the hits stay equal" "equal to the naive scan" "$OUT"

# --- the shipped fixture --------------------------------------------------------------
run "$PY" -m "$MODULE" scan --patterns fixtures/patterns.txt --text "$TEXT"
check_equal "the fixture sweeps" 0 "$STATUS"
LINES=$(grep -cv '^#\|^$' fixtures/patterns.txt)
if [[ "$LINES" -ge 6 ]]; then ok "the fixture holds a set ($LINES patterns)"; else bad "the fixture is too small ($LINES)"; fi

# --- the invariants ---------------------------------------------------------------------
run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
