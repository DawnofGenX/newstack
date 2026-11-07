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

# --- seating keys, walk equal to the sort ------------------------------------------
run "$PY" -m "$MODULE" iter --keys fixtures/keys.txt
check_equal "a walk exits zero" 0 "$STATUS"
check_contains "the walk is named" "keys       16" "$OUT"

run "$PY" -m "$MODULE" iter --keys fixtures/keys.txt --json
WANT=$("$PY" -c 'import json,sys; keys=[int(l.split()[0]) for l in open(sys.argv[1]) if l.strip() and not l.startswith("#")]; print(json.dumps(sorted(keys)))' fixtures/keys.txt)
WALK=$("$PY" -c 'import json,sys; print(json.dumps(json.loads(sys.argv[1])["walk"]))' "$OUT")
check_equal "the walk is the plain sort" "$WANT" "$WALK"

run "$PY" -m "$MODULE" add --keys fixtures/keys.txt 1000
check_equal "an add exits zero" 0 "$STATUS"
check_contains "the add grew the tree" "keys       17" "$OUT"
check_contains "the added key rides to the root" "root       1000" "$OUT"

run "$PY" -m "$MODULE" add --keys fixtures/keys.txt 42
check_equal "a double add exits zero" 0 "$STATUS"
check_contains "a double add sat in once" "keys       16" "$OUT"
check_contains "a double add still rides up" "root       42" "$OUT"

run "$PY" -m "$MODULE" remove --keys fixtures/keys.txt 42
check_equal "a remove exits zero" 0 "$STATUS"
check_contains "the remove shrank the tree" "keys       15" "$OUT"

run "$PY" -m "$MODULE" remove --keys fixtures/keys.txt 4242
check_equal "an absent remove exits two" 2 "$STATUS"
check_contains "the absence is named" "no key 4242" "$OUT"

# --- touches and the rides ------------------------------------------------------------
run "$PY" -m "$MODULE" has --keys fixtures/keys.txt 99
check_equal "a seated key exits zero" 0 "$STATUS"
check_contains "the seat is admitted" "seated     True" "$OUT"
check_contains "the touch left the key at the root" "root       99" "$OUT"

run "$PY" -m "$MODULE" has --keys fixtures/keys.txt 12345
check_equal "an absent key exits one" 1 "$STATUS"
check_contains "the nothing is named" "seated     False" "$OUT"

run "$PY" -m "$MODULE" min --keys fixtures/keys.txt --json
MINK=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["min"])' "$OUT")
ROOTK=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["root"])' "$OUT")
check_equal "the min rides to the root" "$MINK" "$ROOTK"

run "$PY" -m "$MODULE" max --keys fixtures/keys.txt --json
MAXK=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["max"])' "$OUT")
ROOTK=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["root"])' "$OUT")
check_equal "the max rides to the root" "$MAXK" "$ROOTK"

# --- the edges the gate refuses ------------------------------------------------------
run "$PY" -m "$MODULE" iter --keys "$WORK/missing.txt"
check_equal "a missing key list is unusable" 2 "$STATUS"
check_contains "the file is named" "no such key list" "$OUT"

NOISE="$WORK/noise.txt"
printf '7\n1.5\n' >"$NOISE"
run "$PY" -m "$MODULE" iter --keys "$NOISE"
check_equal "a noisy key list is unusable" 2 "$STATUS"
check_contains "the noise is named" "not an integer" "$OUT"

# --- the fixture corpus ---------------------------------------------------------------
COUNT=$(grep -cvE '^[[:space:]]*(#|$)' fixtures/keys.txt)
if [[ "$COUNT" -ge 12 ]]; then
  ok "the fixture holds a corpus ($COUNT keys)"
else
  bad "the fixture is too small ($COUNT keys)"
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
