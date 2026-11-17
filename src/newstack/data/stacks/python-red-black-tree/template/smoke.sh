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
run "$PY" -m "$MODULE" has --keys fixtures/keys.txt 4
check_equal "a held key exits zero" 0 "$STATUS"
check_contains "the key answers as a key" "4            key" "$OUT"

run "$PY" -m "$MODULE" has --keys fixtures/keys.txt 99
check_equal "an absent key exits one" 1 "$STATUS"
check_contains "the absence is named" "not a key" "$OUT"

run "$PY" -m "$MODULE" has --keys fixtures/keys.txt 4 8
check_equal "every key asked must be held" 0 "$STATUS"

run "$PY" -m "$MODULE" has --keys fixtures/keys.txt 4 99
check_equal "one absent key fails the batch" 1 "$STATUS"

# --- the walk ----------------------------------------------------------------------
run "$PY" -m "$MODULE" iter --keys fixtures/keys.txt
check_equal "the walk exits zero" 0 "$STATUS"
check_contains "the walk names its size" "48 listed, ascending" "$OUT"
check_contains "the walk starts at the floor" "  -57" "$OUT"

run "$PY" -m "$MODULE" iter --keys fixtures/keys.txt --json
SHAPE=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["walk"][:3])' "$OUT")
check_equal "the json walks ascending" "[-57, -53, -52]" "$SHAPE"

EMPTY="$WORK/empty.txt"
: >"$EMPTY"
run "$PY" -m "$MODULE" iter --keys "$EMPTY"
check_equal "an empty walk admits it" 1 "$STATUS"

# --- the keys the gate refuses -------------------------------------------------------
run "$PY" -m "$MODULE" has --keys fixtures/keys.txt 1.5
check_equal "a half key is refused by name" 2 "$STATUS"
check_contains "the refusal names the key" "not a key" "$OUT"

run "$PY" -m "$MODULE" iter --keys "$WORK/missing.txt"
check_equal "a missing key list is unusable" 2 "$STATUS"
check_contains "the file is named" "no such key list" "$OUT"

NOISE="$WORK/noise.txt"
printf '1\nabc\n' >"$NOISE"
run "$PY" -m "$MODULE" iter --keys "$NOISE"
check_equal "a noisy key list is unusable" 2 "$STATUS"
check_contains "the noise is named" "not a key" "$OUT"

# --- building and dropping ------------------------------------------------------------
KEYS="$WORK/keys.txt"
printf '# a comment\n\n1\n2\n3\n' >"$KEYS"
run "$PY" -m "$MODULE" add --keys "$KEYS" 9
check_equal "an add exits zero" 0 "$STATUS"
check_contains "the tree names its size" "keys       4 held, 1 added" "$OUT"

run "$PY" -m "$MODULE" add --keys "$KEYS" 1
check_equal "a doubled key is seated once" 0 "$STATUS"
check_contains "the add reports nothing new" "0 added" "$OUT"

run "$PY" -m "$MODULE" remove --keys "$KEYS" 3
check_equal "a removal exits zero" 0 "$STATUS"
check_contains "the removal is named" "removed" "$OUT"

run "$PY" -m "$MODULE" remove --keys "$KEYS" 77
check_equal "remove of an absent key is unusable" 2 "$STATUS"
check_contains "the refusal names the key" "remove of an absent key" "$OUT"

run "$PY" -m "$MODULE" iter --keys "$KEYS" --json
LEFT=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["walk"])' "$OUT")
check_equal "the built tree walks sorted" "[1, 2, 3]" "$LEFT"

# --- the fixture corpus ------------------------------------------------------------------
COUNT=$(grep -cE '^[^#[:space:]]' fixtures/keys.txt)
if [[ "$COUNT" -ge 40 ]]; then
  ok "the fixture holds a corpus ($COUNT keys)"
else
  bad "the fixture is too small ($COUNT keys)"
fi

# --- the stories and the invariants ----------------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
