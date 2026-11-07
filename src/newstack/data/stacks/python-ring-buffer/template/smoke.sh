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

# --- the fixture seats a full ring ------------------------------------------------
run "$PY" -m "$MODULE" drain --values fixtures/values.txt --capacity 8
check_equal "a drain exits zero" 0 "$STATUS"
check_contains "the drain is named" "drained    8" "$OUT"

run "$PY" -m "$MODULE" drain --values fixtures/values.txt --capacity 8 --json
WANT=$("$PY" -c 'import json,sys; rows=[int(l.strip()) for l in open(sys.argv[1]) if l.strip() and not l.startswith("#")]; print(json.dumps(rows[-8:]))' fixtures/values.txt)
GOT=$("$PY" -c 'import json,sys; print(json.dumps(json.loads(sys.argv[1])["drained"]))' "$OUT")
check_equal "the drain is the last eight, in order" "$WANT" "$GOT"

run "$PY" -m "$MODULE" push --values fixtures/values.txt --capacity 8 4242
check_equal "a push exits zero" 0 "$STATUS"
check_contains "the push seats the newest" "pushed     4242" "$OUT"
check_contains "the push drops the oldest" "count      8" "$OUT"

OLDEST=$("$PY" -c 'import json,sys; rows=[int(l.strip()) for l in open(sys.argv[1]) if l.strip() and not l.startswith("#")]; print(json.dumps(rows[-8:])[1:-1].split(",")[0])' fixtures/values.txt)
run "$PY" -m "$MODULE" push --values fixtures/values.txt --capacity 8 4242 --json
DROPPED=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["dropped"])' "$OUT")
check_equal "the drop is exactly the oldest" "$OLDEST" "$DROPPED"

run "$PY" -m "$MODULE" pop --values fixtures/values.txt --capacity 8
check_equal "a pop exits zero" 0 "$STATUS"
check_contains "the pop hands back the oldest" "popped     $OLDEST" "$OUT"

run "$PY" -m "$MODULE" peek --values fixtures/values.txt --capacity 8 --json
PEEKED=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["oldest"])' "$OUT")
check_equal "the peek is the oldest" "$OLDEST" "$PEEKED"

run "$PY" -m "$MODULE" count --values fixtures/values.txt --capacity 8
check_equal "the count exits zero" 0 "$STATUS"
check_contains "the count fills the ring" "count      8" "$OUT"

# --- capacity one, the edge that wraps every push ----------------------------------
run "$PY" -m "$MODULE" peek --values fixtures/values.txt --capacity 1
check_equal "capacity one exits zero" 0 "$STATUS"
LAST=$("$PY" -c 'import sys; rows=[int(l.strip()) for l in open(sys.argv[1]) if l.strip() and not l.startswith("#")]; print(rows[-1])' fixtures/values.txt)
check_contains "capacity one keeps only the newest" "oldest     $LAST" "$OUT"

# --- the edges the gate refuses -----------------------------------------------------
run "$PY" -m "$MODULE" drain --values "$WORK/missing.txt"
check_equal "a missing value list is unusable" 2 "$STATUS"
check_contains "the file is named" "no such value list" "$OUT"

NOISE="$WORK/noise.txt"
printf '7\n1.5\n' >"$NOISE"
run "$PY" -m "$MODULE" drain --values "$NOISE"
check_equal "a noisy value list is unusable" 2 "$STATUS"
check_contains "the noise is named" "not an integer" "$OUT"

run "$PY" -m "$MODULE" drain --values fixtures/values.txt --capacity 0
check_equal "a zero-capacity ring is unusable" 2 "$STATUS"
check_contains "the capacity is named" "positive integer" "$OUT"

# --- the fixture corpus --------------------------------------------------------------
COUNT=$(grep -cvE '^[[:space:]]*(#|$)' fixtures/values.txt)
if [[ "$COUNT" -ge 12 ]]; then
  ok "the fixture holds a corpus ($COUNT values)"
else
  bad "the fixture is too small ($COUNT values)"
fi

# --- the stories and the invariants ---------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
