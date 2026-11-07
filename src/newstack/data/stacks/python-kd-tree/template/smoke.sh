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

# --- membership ------------------------------------------------------------------
run "$PY" -m "$MODULE" has --points fixtures/points.txt 18,7
check_equal "a held point exits zero" 0 "$STATUS"
check_contains "the point answers as a point" "(18, 7)      point" "$OUT"

run "$PY" -m "$MODULE" has --points fixtures/points.txt 99,99
check_equal "an absent point exits one" 1 "$STATUS"
check_contains "the absence is named" "99, 99)     not a point" "$OUT"

run "$PY" -m "$MODULE" has --points fixtures/points.txt 18,7 20,6
check_equal "every point asked must be held" 0 "$STATUS"

run "$PY" -m "$MODULE" has --points fixtures/points.txt 18,7 99,99
check_equal "one absent point fails the batch" 1 "$STATUS"

# --- nearest ---------------------------------------------------------------------
run "$PY" -m "$MODULE" nearest --points fixtures/points.txt 9,9
check_equal "nearest exits zero" 0 "$STATUS"
check_contains "the answer is the argmin" "nearest    (18, 7) at 85 squared" "$OUT"

run "$PY" -m "$MODULE" nearest --points fixtures/points.txt 9,9 --json
SHAPE=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["nearest"])' "$OUT")
check_equal "the json names the point" "[18, 7]" "$SHAPE"

# --- rectangle answers -------------------------------------------------------------
run "$PY" -m "$MODULE" range --points fixtures/points.txt 0,0,25,25
check_equal "a listing exits zero" 0 "$STATUS"
check_contains "the box names its points" "inside     4 point(s)" "$OUT"
check_contains "a listed point shows" "  (18, 7)" "$OUT"

run "$PY" -m "$MODULE" range --points fixtures/points.txt 0,0,25,25 --json
SHAPE=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["listing"])' "$OUT")
check_equal "the listing is sorted" \
  "[[12, 24], [18, 7], [20, 6], [23, 5]]" "$SHAPE"

run "$PY" -m "$MODULE" range --points fixtures/points.txt 100,100,200,200
check_equal "an empty box admits it" 1 "$STATUS"
check_contains "the emptiness is named" "inside     0 point(s)" "$OUT"

# --- the points the gate refuses -----------------------------------------------------
run "$PY" -m "$MODULE" has --points fixtures/points.txt 1.5,2
check_equal "a half-point is refused by name" 2 "$STATUS"
check_contains "the refusal names the pair" "not a point" "$OUT"

run "$PY" -m "$MODULE" count --points "$WORK/missing.txt"
check_equal "a missing point list is unusable" 2 "$STATUS"
check_contains "the file is named" "no such point list" "$OUT"

NOISE="$WORK/noise.txt"
printf '1,2\n3,4,5\n' >"$NOISE"
run "$PY" -m "$MODULE" count --points "$NOISE"
check_equal "a noisy point list is unusable" 2 "$STATUS"
check_contains "the noise is named" "not a point" "$OUT"

# --- building and seating --------------------------------------------------------------
POINTS="$WORK/points.txt"
printf '# a comment\n\n1,1\n2,2\n3,3\n' >"$POINTS"
run "$PY" -m "$MODULE" add --points "$POINTS" 9,9
check_equal "an add exits zero" 0 "$STATUS"
check_contains "the tree names its size" "points     4 held, 1 added" "$OUT"

run "$PY" -m "$MODULE" add --points "$POINTS" 1,1
check_equal "a doubled point is seated once" 0 "$STATUS"
check_contains "the add reports nothing new" "0 added" "$OUT"

run "$PY" -m "$MODULE" nearest --points "$POINTS" 0,0
check_contains "the nearest of the built tree" "nearest    (1, 1) at 2 squared" "$OUT"

# --- count and the seating -----------------------------------------------------------------
run "$PY" -m "$MODULE" count --points fixtures/points.txt
check_equal "the count exits zero" 0 "$STATUS"
check_contains "the count names the size" "points     50 held" "$OUT"
check_contains "the splits still divide" "seated     True, splits divide" "$OUT"

# --- the fixture corpus ----------------------------------------------------------------------
COUNT=$(grep -cE '^[^#[:space:]]' fixtures/points.txt)
if [[ "$COUNT" -ge 40 ]]; then
  ok "the fixture holds a corpus ($COUNT points)"
else
  bad "the fixture is too small ($COUNT points)"
fi

# --- the stories and the invariants --------------------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
