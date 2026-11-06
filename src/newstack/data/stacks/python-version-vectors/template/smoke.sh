#!/usr/bin/env bash
# Exercise the command line the way a user would: real vectors, real exit codes.
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

check "an ordered pair compares" run compare --left a:1 --right a:2
check_contains "the ordered pair says before" "relation     before"

check_status "a concurrent pair exits one" 1 run compare --left a:1 --right b:2
check_contains "a concurrent pair explains itself" "neither write saw the other"

check "an equal pair compares" run compare --left a:2,b:1 --right b:1,a:2
check_contains "an equal pair says equal" "relation     equal"

check "a merge runs" run merge --left a:2 --right b:3
check_contains "the merge is the pointwise maximum" "merged       a:2,b:3"

check "a vector above the floor is sound" run prune --vector a:4,b:2 --floor a:3,b:2
check_contains "the sound vector keeps the counter above the floor" "compacted    a:4"

check_status "a vector below the floor exits one" 1 run prune --vector a:2,b:2 --floor a:3,b:2
check_contains "the unsafe vector says so" "sound        NO"

check_status "the fixture matrix reports concurrency" 1 run pairs --vectors fixtures/vectors.jsonl
check_contains "the matrix names a concurrent pair" "concurrent    4 pair(s)"

printf '{"name": "x", "vector": "a:1"}\n{"name": "y", "vector": "a:2"}\n' >"$WORK/chain.jsonl"
check "a consistent file exits zero" run pairs --vectors "$WORK/chain.jsonl"
check_contains "the consistent file has no concurrency" "concurrent    0 pair(s)"

check "compare can print json" run compare --left a:1 --right a:2 --json
run compare --left a:1 --right a:2 --json >"$WORK/compare.json" 2>/dev/null
if "$PY" -c 'import json,sys; data=json.load(open(sys.argv[1])); assert data["relation"]=="before"' "$WORK/compare.json"; then
  ok "the json parses"
else
  bad "the json parses" "the file is not the object the command promised"
fi

check_status "a malformed vector is a usage error" 2 run compare --left a --right a:1
check_status "a missing vector file is a usage error" 2 run pairs --vectors "$WORK/nowhere.jsonl"
check_status "an unknown command is unusable" 2 run order --left a:1

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
