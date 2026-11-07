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

# --- building a ladder ------------------------------------------------------------
run "$PY" -m "$MODULE" build --count 32
check_equal "the build exits zero" 0 "$STATUS"
check_contains "the build names the shape" "size 32 bound 12 nodes" "$OUT"

run "$PY" -m "$MODULE" build --values fixtures/values.txt
check_equal "the codex builds" 0 "$STATUS"
check_contains "the codex folds whole" "root 1855 invariant True" "$OUT"

# --- windows answer as their slices sum ----------------------------------------------
run "$PY" -m "$MODULE" query --values fixtures/values.txt 3 10
check_equal "a window exits zero" 0 "$STATUS"
check_contains "the window answers its slice" "[3, 10) = 11 visits 3 bound 10" "$OUT"

run "$PY" -m "$MODULE" query --values fixtures/values.txt 4 4
check_equal "the empty window answers zero" 0 "$STATUS"
check_contains "the identity visits nothing" "= 0 visits 0 bound 10" "$OUT"

run "$PY" -m "$MODULE" query --values fixtures/values.txt 0 30
check_contains "the full window answers the total" "= 1855 visits 4 bound 10" "$OUT"

run "$PY" -m "$MODULE" query --values fixtures/values.txt 0 31
check_equal "a window past the end is reported" 1 "$STATUS"
check_contains "the refusal names the window" "not inside" "$OUT"

# --- the seam switches the fold --------------------------------------------------------
run "$PY" -m "$MODULE" query --mode min --values fixtures/values.txt 3 10
check_contains "the same walk answers a floor" "[3, 10) = -5 visits 3 bound 10" "$OUT"

# --- edits re-fold the path ---------------------------------------------------------------
run "$PY" -m "$MODULE" set --values fixtures/values.txt 4 40
check_equal "a set exits zero" 0 "$STATUS"
check_contains "the set lands and refolds" "set    4 -> 40 root 1900 invariant True" "$OUT"

run "$PY" -m "$MODULE" add --values fixtures/values.txt 9 -10
check_equal "an add exits zero" 0 "$STATUS"
check_contains "the add slides and refolds" "add    9 by -10 -> -7 root 1845 invariant True" "$OUT"

run "$PY" -m "$MODULE" set --values fixtures/values.txt 30 1
check_equal "an index past the end is reported" 1 "$STATUS"
check_contains "the refusal names the index" "outside" "$OUT"

# --- the codex as input ---------------------------------------------------------------------
run "$PY" -m "$MODULE" build --values "$WORK/missing.txt"
check_equal "a missing codex is unusable" 2 "$STATUS"
check_contains "the file is named" "cannot read" "$OUT"

NOISE="$WORK/noise.txt"
printf 'one two\n' >"$NOISE"
run "$PY" -m "$MODULE" build --values "$NOISE"
check_equal "a codex of noise is unusable" 2 "$STATUS"
check_contains "the noise is named" "exactly one value" "$OUT"

FIXTURE_CODEX=fixtures/values.txt
COUNT=$(grep -cv '^\s*\(#\|$\)' "$FIXTURE_CODEX")
if [[ "$COUNT" -ge 20 ]]; then
  ok "the fixture holds an array ($COUNT values)"
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
