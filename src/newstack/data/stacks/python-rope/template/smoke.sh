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

# --- the spine ------------------------------------------------------------------
TEXT="$WORK/text.txt"
printf '# a note\nalpha bravo charlie\ndelta echo\n' >"$TEXT"

run "$PY" -m "$MODULE" load --text "$TEXT"
check_equal "load exits zero" 0 "$STATUS"
check_contains "the spine is stated" "balanced   True" "$OUT"
check_contains "the text survives the read" "alpha bravo charlie" "$OUT"

run "$PY" -m "$MODULE" load --text "$TEXT" --json
SIZE=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["size"])' "$OUT")
check_equal "load --json counts the text" "30" "$SIZE"

run "$PY" -m "$MODULE" load --text "$WORK/missing.txt"
check_equal "a missing text is unusable" 2 "$STATUS"
check_contains "the file is named" "no such text" "$OUT"

# --- the window -------------------------------------------------------------------
run "$PY" -m "$MODULE" slice --text "$TEXT" --start 6 --stop 11
check_equal "a window exits zero" 0 "$STATUS"
check_contains "the window is stated" "window     [6..11)" "$OUT"
check_contains "the window holds the word" "bravo" "$OUT"

run "$PY" -m "$MODULE" slice --text "$TEXT" --start 5 --stop 5
check_equal "an empty window answers none" 1 "$STATUS"

run "$PY" -m "$MODULE" slice --text "$TEXT" --start 9 --stop 2
check_equal "an inverted window is unusable" 2 "$STATUS"
check_contains "the inversion is named" "sits below" "$OUT"

# --- pairing and cutting -------------------------------------------------------------
OTHER="$WORK/other.txt"
printf 'omega\n' >"$OTHER"
run "$PY" -m "$MODULE" join --text "$TEXT" --other "$OTHER"
check_equal "a join exits zero" 0 "$STATUS"
check_contains "the join is the pair in order" "delta echoomega" "$OUT"

run "$PY" -m "$MODULE" split --text "$TEXT" --at 5
check_equal "a cut exits zero" 0 "$STATUS"
check_contains "the cut rejoins" "rejoined   True" "$OUT"

# --- the fixture corpus -----------------------------------------------------------------
run "$PY" -m "$MODULE" load --text fixtures/text.txt
check_equal "the fixture reads as a text" 0 "$STATUS"
check_contains "the fixture keeps its paragraphs" "yankee zulu" "$OUT"

# --- the invariants ------------------------------------------------------------------------
run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
