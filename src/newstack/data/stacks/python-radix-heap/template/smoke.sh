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

# --- building a heap ------------------------------------------------------------
run "$PY" -m "$MODULE" build --count 32
check_equal "the build exits zero" 0 "$STATUS"
check_contains "the build names the size" "size 32" "$OUT"
check_contains "the build counts its buckets" "buckets hold keys" "$OUT"

run "$PY" -m "$MODULE" build --keys fixtures/keys.txt
check_equal "the codex builds" 0 "$STATUS"
check_contains "the codex is forty-six keys" "size 46" "$OUT"
check_contains "the seating invariant holds" "invariant True" "$OUT"

# --- pop-min answers sorted -------------------------------------------------------
run "$PY" -m "$MODULE" pop --keys fixtures/keys.txt 3
check_equal "the pops exit zero" 0 "$STATUS"
check_contains "the first pop is the floor" "popped   '0' = 0 base 0" "$OUT"
check_contains "the third pop follows its bits" "popped   '15' = 2 base 15" "$OUT"

run "$PY" -m "$MODULE" pop --keys fixtures/keys.txt 99
check_equal "popping past the heap reports it" 1 "$STATUS"
check_contains "the drain is admitted" "drained  empty" "$OUT"

# --- push names the seat ------------------------------------------------------------
run "$PY" -m "$MODULE" push 30
check_equal "a push exits zero" 0 "$STATUS"
check_contains "thirty sits in bucket five" "pushed       30  push bucket 5" "$OUT"

run "$PY" -m "$MODULE" push --keys fixtures/keys.txt 7
check_equal "a push onto a heap exits zero" 0 "$STATUS"
check_contains "the seat is not a rebuild" "rebuilt=False" "$OUT"

run "$PY" -m "$MODULE" push -5
check_equal "a key below the floor is refused" 2 "$STATUS"
check_contains "the refusal names the key" "no key" "$OUT"

# --- key streams ---------------------------------------------------------------------
KEYS="$WORK/keys.txt"
printf '7 70\n8 80\n9 90\n' >"$KEYS"
run "$PY" -m "$MODULE" pop --keys "$KEYS" 1
check_contains "a written stream reads back" "popped   '7' = 70" "$OUT"

run "$PY" -m "$MODULE" build --keys "$WORK/missing.txt"
check_equal "a missing stream is unusable" 2 "$STATUS"
check_contains "the file is named" "cannot read" "$OUT"

NOISE="$WORK/noise.txt"
printf 'one two\n' >"$NOISE"
run "$PY" -m "$MODULE" build --keys "$NOISE"
check_equal "a stream of noise is unusable" 2 "$STATUS"
check_contains "the noise is named" "non-integer" "$OUT"

# --- the fixture stream -----------------------------------------------------------------
FIXTURE_STREAM=fixtures/keys.txt
COUNT=$(grep -cv '^\s*\(#\|$\)' "$FIXTURE_STREAM")
if [[ "$COUNT" -ge 20 ]]; then
  ok "the fixture holds a stream ($COUNT keys)"
else
  bad "the fixture is too small ($COUNT keys)"
fi

# --- the stories and the invariants --------------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
