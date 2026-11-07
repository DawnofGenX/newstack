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

# --- building the table ------------------------------------------------------------
run "$PY" -m "$MODULE" build --texts fixtures/texts.txt
check_equal "a build exits zero" 0 "$STATUS"
check_contains "the text is named" "banana" "$OUT"
check_contains "the starts are seated" "suffixes   6" "$OUT"

run "$PY" -m "$MODULE" build --texts fixtures/texts.txt --json
SHAPE=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["array"])' "$OUT")
check_equal "the array is the slice-sort" "[5, 3, 1, 0, 4, 2]" "$SHAPE"

# --- counting, overlaps honest ------------------------------------------------------
run "$PY" -m "$MODULE" count --texts fixtures/texts.txt na
check_equal "a held pattern exits zero" 0 "$STATUS"
check_contains "the count names the starts" "count      2" "$OUT"

run "$PY" -m "$MODULE" count --texts fixtures/texts.txt zzz
check_equal "an absent pattern exits one" 1 "$STATUS"
check_contains "the absence is admitted" "count      0" "$OUT"

run "$PY" -m "$MODULE" count --texts fixtures/texts.txt na --json
POSITIONS=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["positions"])' "$OUT")
check_equal "starts come in table order" "[4, 2]" "$POSITIONS"

# --- the longest repeat and the shares ----------------------------------------------
run "$PY" -m "$MODULE" lrs --texts fixtures/texts.txt
check_equal "a repeat exits zero" 0 "$STATUS"
check_contains "the repeat is the tall share" "repeat     'ana'" "$OUT"

run "$PY" -m "$MODULE" lcp --texts fixtures/texts.txt 1 3
check_equal "neighbours share by letter" 0 "$STATUS"
check_contains "the share is counted" "shares     3" "$OUT"

run "$PY" -m "$MODULE" lcp --texts fixtures/texts.txt 0 1
check_equal "strangers exit one" 1 "$STATUS"
check_contains "the nothing is named" "shares     0" "$OUT"

# --- the edges the gate refuses ------------------------------------------------------
run "$PY" -m "$MODULE" count --texts fixtures/texts.txt ZZZ
check_equal "uppercase is refused by name" 2 "$STATUS"
check_contains "the refusal names the pattern" "not lowercase" "$OUT"

run "$PY" -m "$MODULE" build --texts "$WORK/missing.txt"
check_equal "a missing text list is unusable" 2 "$STATUS"
check_contains "the file is named" "no such text list" "$OUT"

NOISE="$WORK/noise.txt"
printf 'banana\nban3na\n' >"$NOISE"
run "$PY" -m "$MODULE" build --texts "$NOISE"
check_equal "a noisy text list is unusable" 2 "$STATUS"
check_contains "the noise is named" "non-letter" "$OUT"

run "$PY" -m "$MODULE" lcp --texts fixtures/texts.txt 0 99
check_equal "a place past the text is unusable" 2 "$STATUS"

# --- the fixture corpus ----------------------------------------------------------------
COUNT=$(grep -cvE '^[[:space:]]*(#|$)' fixtures/texts.txt)
if [[ "$COUNT" -ge 12 ]]; then
  ok "the fixture holds a corpus ($COUNT texts)"
else
  bad "the fixture is too small ($COUNT texts)"
fi

# --- the stories and the invariants -----------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
