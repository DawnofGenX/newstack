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
check_contains "help names meld" "meld" "$OUT"

# --- push names the rank ------------------------------------------------------------
run "$PY" -m "$MODULE" push 30
check_equal "a push exits zero" 0 "$STATUS"
check_contains "thirty lands in a rank-zero tree" "push rank 0 linked=False" "$OUT"

run "$PY" -m "$MODULE" push --keys fixtures/keys.txt 7
check_equal "a push onto a forest exits zero" 0 "$STATUS"
check_contains "the key names its rank" "push rank" "$OUT"
check_contains "the forest kept its one-per-rank rule" "bits 101111" "$OUT"

run "$PY" -m "$MODULE" push seven
check_equal "a word is no key" 2 "$STATUS"
check_contains "the refusal names the word" "is no key" "$OUT"

# --- pop-min answers sorted -----------------------------------------------------------
run "$PY" -m "$MODULE" pop --keys fixtures/keys.txt 3
check_equal "the pops exit zero" 0 "$STATUS"
check_contains "the first pop is the floor" "popped   '-120' = 34" "$OUT"
check_contains "the third pop follows the order" "popped   '-13' = 18" "$OUT"

run "$PY" -m "$MODULE" pop --keys fixtures/keys.txt 99
check_equal "popping past the forest reports it" 1 "$STATUS"
check_contains "the drain is admitted" "drained  empty" "$OUT"

# --- meld is the product ---------------------------------------------------------------
run "$PY" -m "$MODULE" meld 1 2 3
check_equal "a meld exits zero" 0 "$STATUS"
check_contains "the union counts both sides" "melded   64 + 3 into 67" "$OUT"
check_contains "the donor gave everything" "donor    0 key(s) left" "$OUT"

run "$PY" -m "$MODULE" meld --keys fixtures/keys.txt nine
check_equal "a meld of words is refused" 2 "$STATUS"

# --- size walks the bit pattern -----------------------------------------------------------
run "$PY" -m "$MODULE" size --keys fixtures/keys.txt
check_equal "the size exits zero" 0 "$STATUS"
check_contains "the count is forty-seven" "size     47" "$OUT"
check_contains "the ranks are the bits" "bits 101111, ranks [0, 1, 2, 3, 5]" "$OUT"
check_contains "the forest stands the invariant" "invariant True" "$OUT"

run "$PY" -m "$MODULE" peek --count 64
check_equal "a peek exits zero" 0 "$STATUS"
check_contains "sixty-four keys stand as rank six" "ranks [6]" "$OUT"

# --- key streams ------------------------------------------------------------------------------
KEYS="$WORK/keys.txt"
printf -- '-7 70\n8 80\n9 90\n' >"$KEYS"
run "$PY" -m "$MODULE" pop --keys "$KEYS" 1
check_contains "a written stream reads back" "popped   '-7' = 70" "$OUT"

run "$PY" -m "$MODULE" size --keys "$WORK/missing.txt"
check_equal "a missing stream is unusable" 2 "$STATUS"
check_contains "the file is named" "cannot read" "$OUT"

NOISE="$WORK/noise.txt"
printf 'one two\n' >"$NOISE"
run "$PY" -m "$MODULE" size --keys "$NOISE"
check_equal "a stream of noise is unusable" 2 "$STATUS"
check_contains "the noise is named" "non-integer" "$OUT"

# --- the fixture stream --------------------------------------------------------------------------
FIXTURE_STREAM=fixtures/keys.txt
COUNT=$(grep -cv '^\s*\(#\|$\)' "$FIXTURE_STREAM")
if [[ "$COUNT" -ge 20 ]]; then
  ok "the fixture holds a stream ($COUNT keys)"
else
  bad "the fixture is too small ($COUNT keys)"
fi

# --- the stories and the invariants ------------------------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
