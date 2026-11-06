#!/usr/bin/env bash
# Exercise the command line the way a user would: real files, real exit codes.
set -uo pipefail

PY="${PY:-.venv/bin/python}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
FIXTURES="$(cd "$(dirname "$0")" && pwd)/fixtures"
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

A="$WORK/a.txt"
B="$WORK/b.txt"
cat >"$A" <<'TEXT'
the quarterly report shows revenue rising across every region while costs stayed flat
for the third quarter in a row and the board asked for a longer forecast
TEXT
cp "$A" "$B"
cat >"$WORK/c.txt" <<'TEXT'
the monsoon arrived late this year so the reservoir levels stayed below average and
the city rationed water through the summer months
TEXT

check "a signature can be printed" run signature --text "$A" --width 32
check_contains "the signature line is labelled" "signature"

check "a signature can be printed as json" run signature --text "$A" --width 16 --json
check_contains "the json carries the width" '"width": 16'

check_status "identical files read as similar" 0 run similar --left "$A" --right "$B"
check_contains "the comparison reports the estimate" "estimate"
check_status "unlike files exit one" 1 run similar --left "$A" --right "$WORK/c.txt"
check_contains "the comparison names the decision" "different"
check "the comparison can be printed as json" run similar --left "$A" --right "$B" --json
check_contains "the json carries the exact jaccard" '"exact": 1.0'

check "candidates reads a corpus" run candidates --corpus "$FIXTURES/corpus.jsonl"
check_contains "the report counts every pair" "possible pairs"
check "candidates can be printed as json" run candidates --corpus "$FIXTURES/corpus.jsonl" --json
check_contains "the json carries the recall" '"recall"'

check_status "dedupe can fail a build on duplicates" 1 \
  run dedupe --corpus "$FIXTURES/corpus.jsonl" --threshold 0.8 --fail-on-duplicates
check_contains "the clustering names its groups" "cluster"
check_status "a stricter threshold passes the same corpus" 0 \
  run dedupe --corpus "$FIXTURES/corpus.jsonl" --threshold 0.95 --fail-on-duplicates

check "a curve can be printed" run curve --width 128 --threshold 0.8
check_contains "the curve names the banding" "banding"
check_contains "the curve prints a probability column" "probability"

check_status "a missing corpus is a usage error" 2 run candidates --corpus "$WORK/absent.jsonl"
check_status "bands without rows is a usage error" 2 \
  run candidates --corpus "$FIXTURES/corpus.jsonl" --bands 8

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
