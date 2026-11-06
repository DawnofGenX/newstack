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

# --- building a tree ------------------------------------------------------------
KEYS="$WORK/keys.txt"
printf '# a comment\n-7\n0\n3\n11\n16\n23\n' >"$KEYS"

run "$PY" -m "$MODULE" load --keys "$KEYS" --order 2
check_equal "load exits zero" 0 "$STATUS"
check_contains "order two keeps the band at one" "band [1..3]" "$OUT"

run "$PY" -m "$MODULE" load --keys "$KEYS" --order 3
check_contains "order three keeps the band at two" "band [2..5]" "$OUT"

run "$PY" -m "$MODULE" load --keys "$KEYS" --json
check_equal "load --json exits zero" 0 "$STATUS"
SHAPE=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["keys"])' "$OUT")
check_equal "the walk is the sorted corpus" "[-7, 0, 3, 11, 16, 23]" "$SHAPE"

run "$PY" -m "$MODULE" load --keys "$WORK/missing.txt"
check_equal "a missing key list is unusable" 2 "$STATUS"
check_contains "the file is named" "no such key list" "$OUT"

run "$PY" -m "$MODULE" load --keys "$KEYS" --order 1
check_equal "order one is unusable" 2 "$STATUS"

# --- exact lookup ----------------------------------------------------------------
run "$PY" -m "$MODULE" lookup --keys "$KEYS" --key 11
check_equal "a held key exits zero" 0 "$STATUS"
check_contains "the held key is named" "held       True" "$OUT"

run "$PY" -m "$MODULE" lookup --keys "$KEYS" --key 12
check_equal "a missing key exits one" 1 "$STATUS"

run "$PY" -m "$MODULE" lookup --keys "$KEYS" --key 11 --json
LOOKED=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["held"])' "$OUT")
check_equal "lookup --json is only json" "True" "$LOOKED"

# --- the window --------------------------------------------------------------------
run "$PY" -m "$MODULE" scan --keys "$KEYS" --low 0 --high 12
check_equal "a full window exits zero" 0 "$STATUS"
check_contains "the window is stated" "window     [0..12]" "$OUT"

run "$PY" -m "$MODULE" scan --keys "$KEYS" --low 4 --high 10
check_equal "an empty window exits one" 1 "$STATUS"

run "$PY" -m "$MODULE" scan --keys "$KEYS" --low 20 --high 3
check_equal "an inverted window is unusable" 2 "$STATUS"
check_contains "the inversion is named" "sits above" "$OUT"

# --- the page file -------------------------------------------------------------------
run "$PY" -m "$MODULE" page --keys "$KEYS" --out "$WORK/tree.page"
check_equal "the freeze exits zero" 0 "$STATUS"
check_contains "the read-back is identical" "identical  True" "$OUT"
if [[ -s "$WORK/tree.page" ]]; then ok "the page file was written"; else bad "the page file is empty"; fi

# --- the fixture corpus ----------------------------------------------------------------
HITS=0
while IFS= read -r key; do
  [[ -z "$key" || "$key" == \#* ]] && continue
  HITS=$((HITS + 1))
  run "$PY" -m "$MODULE" lookup --keys fixtures/keys.txt --key "$key"
  if [[ "$STATUS" -eq 0 ]]; then ok "fixture $key is held"; else bad "fixture $key was lost"; fi
done <fixtures/keys.txt
if [[ "$HITS" -ge 20 ]]; then ok "the fixture holds a corpus ($HITS keys)"; else bad "the fixture is too small ($HITS keys)"; fi

# --- the invariants ---------------------------------------------------------------------
run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
