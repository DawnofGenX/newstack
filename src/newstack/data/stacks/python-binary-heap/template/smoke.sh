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

# --- seating keys, the drain equal to the sort ----------------------------------------
run "$PY" -m "$MODULE" len --keys fixtures/keys.txt
check_equal "a len exits zero" 0 "$STATUS"
check_contains "the heap counts its keys" "keys       16" "$OUT"

run "$PY" -m "$MODULE" peek --keys fixtures/keys.txt --json
HEAD=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["head"])' "$OUT")
MINK=$("$PY" -c 'import json,sys; keys=[int(l.split()[0]) for l in open(sys.argv[1]) if l.strip() and not l.startswith("#")]; print(min(keys))' fixtures/keys.txt)
check_equal "the head is the minimum of the bag" "$MINK" "$HEAD"

run "$PY" -m "$MODULE" push --keys fixtures/keys.txt 1000
check_equal "a push exits zero" 0 "$STATUS"
check_contains "the push grew the heap" "keys       17" "$OUT"
check_contains "a small key keeps the head" "head       -999" "$OUT"

run "$PY" -m "$MODULE" push --keys fixtures/keys.txt -5000
check_equal "a smaller push exits zero" 0 "$STATUS"
check_contains "the smaller key took the head" "head       -5000" "$OUT"

run "$PY" -m "$MODULE" pop --keys fixtures/keys.txt --json
POPPED=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["popped"])' "$OUT")
check_equal "a pop hands over the minimum" "$MINK" "$POPPED"
LEFT=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["keys"])' "$OUT")
check_equal "the pop left one seat fewer" 15 "$LEFT"

ONE="$WORK/one.txt"
printf '7\n' >"$ONE"
run "$PY" -m "$MODULE" pop --keys "$ONE"
check_equal "a single-key pop exits zero" 0 "$STATUS"
check_contains "the single key is handed over" "popped     7" "$OUT"
check_contains "the heap is left empty" "keys       0" "$OUT"

run "$PY" -m "$MODULE" pop --keys "$WORK/nothing.txt"
check_equal "a missing key list is unusable" 2 "$STATUS"
check_contains "the file is named" "no such key list" "$OUT"

# --- the fixture corpus ----------------------------------------------------------------
COUNT=$(grep -cvE '^[[:space:]]*(#|$)' fixtures/keys.txt)
if [[ "$COUNT" -ge 12 ]]; then
  ok "the fixture holds a corpus ($COUNT keys)"
else
  bad "the fixture is too small ($COUNT keys)"
fi

# --- the storm the smoke itself runs ----------------------------------------------------
STORM_OUT=$("$PY" -c '
import random
from {{ package_name }}.heap import MinHeap
rng = random.Random(4)
pool = rng.sample(range(-500, 500), 40)
heap = MinHeap()
live: list[int] = []
breaks = 0
for _ in range(200):
    if rng.random() < 0.55 or not live:
        key = rng.choice(pool)
        heap.push(key)
        live.append(key)
    else:
        got = heap.pop()
        live.remove(got)
    if heap.breaks() or (live and heap.peek() != min(live)):
        breaks += 1
drain_ok = heap.drain() == sorted(live)
print(f"breaks={breaks} drain-equal-sort={drain_ok}")
')
check_contains "two hundred moves, the rule unbroken" "breaks=0" "$STORM_OUT"
check_contains "the drain spelled the plain sort" "drain-equal-sort=True" "$STORM_OUT"

# --- the edges the gate refuses ---------------------------------------------------------
run "$PY" -m "$MODULE" len --keys "$WORK/missing.txt"
check_equal "a missing key list is unusable" 2 "$STATUS"
check_contains "the file is named" "no such key list" "$OUT"

NOISE="$WORK/noise.txt"
printf '7\n1.5\n' >"$NOISE"
run "$PY" -m "$MODULE" len --keys "$NOISE"
check_equal "a noisy key list is unusable" 2 "$STATUS"
check_contains "the noise is named" "not an integer" "$OUT"

# --- the stories and the invariants ------------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
