#!/usr/bin/env bash
# Exercise the command line the way a user would: real traces, real exit codes.
set -uo pipefail

PY="${PY:-.venv/bin/python}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

passed=0
failed=0

ok() {
  passed=$((passed + 1))
  printf 'ok   %s\n' "$1"
}

bad() {
  failed=$((failed + 1))
  printf 'FAIL %s\n' "$1"
  if [ $# -gt 1 ]; then
    printf '     %s\n' "$2"
  fi
}

check() {
  local name="$1"
  shift
  if "$@" >"$WORK/out" 2>"$WORK/err"; then
    ok "$name"
  else
    bad "$name" "$(tail -n 2 "$WORK/err" "$WORK/out" 2>/dev/null | tr '\n' ' ')"
  fi
}

check_status() {
  local name="$1"
  local expected="$2"
  shift 2
  "$@" >"$WORK/out" 2>"$WORK/err"
  local status=$?
  if [ "$status" -eq "$expected" ]; then
    ok "$name"
  else
    bad "$name" "expected exit $expected, got $status: $(tail -n 1 "$WORK/err" "$WORK/out" | tr '\n' ' ')"
  fi
}

check_contains() {
  local name="$1"
  local needle="$2"
  if grep -qF -- "$needle" "$WORK/out"; then
    ok "$name"
  else
    bad "$name" "no '$needle' in: $(head -n 3 "$WORK/out" | tr '\n' ' ')"
  fi
}

run() {
  "$PY" -m "$MODULE" "$@"
}

check "the version banner names the program" run --version
check_contains "the banner carries the program name" "$PROGRAM "

check "help is available" run --help

check "a simulation runs" run simulate --policy lru --trace zipf --accesses 2000
check_contains "the simulation prints the ceiling" "ceiling"
check_contains "the simulation prints the policy row" "lru"

check "a simulation can be gated" run simulate --accesses 2000 --min-hit-rate 0.0
check_status "a missed gate exits one" 1 run simulate --accesses 2000 --min-hit-rate 0.99
check_contains "a missed gate says BREACH" "BREACH"

check "a comparison runs" run compare --accesses 2000
check_contains "the comparison names a best policy" "best"
check_contains "the comparison prints every policy" "slru"

check "a curve runs" run curve --capacities 10,50 --accesses 2000
check_contains "the curve prints both capacities" "      10"

check "simulate can be printed as json" run simulate --accesses 1000 --json
check_contains "the json carries the access count" '"accesses": 1000'
check_contains "the json carries the ceiling" '"ceiling"'
run simulate --accesses 500 --json >"$WORK/sim.json" 2>/dev/null
if "$PY" -c 'import json,sys; data=json.load(open(sys.argv[1])); assert data["accesses"]==500' "$WORK/sim.json"; then
  ok "the json parses"
else
  bad "the json parses" "the file is not the object the command promised"
fi

check_status "an unknown trace is a usage error" 2 run simulate --trace spiral
check_status "an unknown policy is a usage error" 2 run simulate --policy mru
check_status "unreadable capacities are a usage error" 2 run curve --capacities ten
check_status "a zero capacity is unusable" 2 run simulate --capacity 0

if run demo >"$WORK/demo" 2>"$WORK/demo-err"; then
  ok "the demo runs"
else
  bad "the demo runs" "$(tail -n 2 "$WORK/demo-err" | tr '\n' ' ')"
fi
holds=$(grep -c -- '  -> holds' "$WORK/demo")
if [ "$holds" -eq 6 ]; then
  ok "all six stories hold"
else
  bad "all six stories hold" "only $holds of 6 held"
fi

check "the selftest passes" run selftest
check_contains "the selftest reports its checks" "checks passed"

printf '\nsmoke: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
