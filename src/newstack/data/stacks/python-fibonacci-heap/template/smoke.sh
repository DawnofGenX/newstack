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
check_contains "help names the decrease" "decrease" "$OUT"

# --- pushing, popping, decreasing: the drain is the sort ---------------------------
run "$PY" -m "$MODULE" size --items fixtures/items.txt
check_equal "a size exits zero" 0 "$STATUS"
check_contains "the size is named" "items      16" "$OUT"

run "$PY" -m "$MODULE" peek --items fixtures/items.txt --json
MIN=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["min"])' "$OUT")
WANT=$("$PY" -c 'import json,sys; keys=[int(l.split()[0]) for l in open(sys.argv[1]) if l.strip() and not l.startswith("#")]; print(json.dumps(sorted(keys)))' fixtures/items.txt)
KEYS=$("$PY" -c 'import json,sys; print(json.dumps(json.loads(sys.argv[1])["keys"]))' "$OUT")
check_equal "the live keys are the plain sort" "$WANT" "$KEYS"
check_contains "the peek is the plain min" "-999" "$MIN"

run "$PY" -m "$MODULE" push --items fixtures/items.txt 1000
check_equal "a push exits zero" 0 "$STATUS"
check_contains "the push grew the heap" "items      17" "$OUT"
check_contains "the push handed a handle" "item       17" "$OUT"

run "$PY" -m "$MODULE" pop --items fixtures/items.txt
check_equal "a pop exits zero" 0 "$STATUS"
check_contains "the pop released the min" "released   -999" "$OUT"
check_contains "the pop shrank the heap" "items      15" "$OUT"

run "$PY" -m "$MODULE" decrease --items fixtures/items.txt 2 -4000
check_equal "a decrease exits zero" 0 "$STATUS"
check_contains "the drop took the min seat" "min        -4000" "$OUT"

run "$PY" -m "$MODULE" decrease --items fixtures/items.txt 1 999999
check_equal "an increase sold as a decrease exits two" 2 "$STATUS"
check_contains "the increase is named" "not a decrease" "$OUT"

run "$PY" -m "$MODULE" decrease --items fixtures/items.txt 99 5
check_equal "an absent item exits two" 2 "$STATUS"
check_contains "the absence is named" "no item 99" "$OUT"

# --- the edges the gate refuses -----------------------------------------------------
EMPTY="$WORK/empty.txt"
printf '# nothing but a comment\n' >"$EMPTY"
run "$PY" -m "$MODULE" peek --items "$EMPTY"
check_equal "an empty heap peek exits one" 1 "$STATUS"
check_contains "the emptiness is named" "the heap is empty" "$OUT"

run "$PY" -m "$MODULE" size --items "$WORK/missing.txt"
check_equal "a missing item list is unusable" 2 "$STATUS"
check_contains "the file is named" "no such item list" "$OUT"

NOISE="$WORK/noise.txt"
printf '7\n1.5\n' >"$NOISE"
run "$PY" -m "$MODULE" size --items "$NOISE"
check_equal "a noisy item list is unusable" 2 "$STATUS"
check_contains "the noise is named" "not an integer" "$OUT"

# --- the fixture corpus --------------------------------------------------------------
COUNT=$(grep -cvE '^[[:space:]]*(#|$)' fixtures/items.txt)
if [[ "$COUNT" -ge 12 ]]; then
  ok "the fixture holds a corpus ($COUNT items)"
else
  bad "the fixture is too small ($COUNT items)"
fi

# --- the stories and the invariants ----------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
