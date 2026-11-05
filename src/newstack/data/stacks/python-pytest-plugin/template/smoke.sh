#!/usr/bin/env bash
# End-to-end: the plugin writes a report, the console script reads it, strict mode refuses.
#
#   PY=.venv/bin/python bash smoke.sh
#
# Deliberately without `set -e`: a smoke test that stops at the first failure hides the
# other nine things that are also broken.
set -uo pipefail

PY="${PY:-python}"
PROGRAM="$(dirname "$0")/.venv/bin/{{ npm_name }}"
[ -x "$PROGRAM" ] || PROGRAM="$PY -m {{ package_name }}"
cd "$(dirname "$0")"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
checks=0
failures=0

ok() {
  checks=$((checks + 1))
  printf 'ok   %s\n' "$1"
}

fail() {
  checks=$((checks + 1))
  failures=$((failures + 1))
  printf 'FAIL %s\n' "$1"
  [ $# -gt 1 ] && printf '     %s\n' "$2"
}

expect() {
  local name="$1" want="$2"
  shift 2
  "$@" >"$work/out" 2>"$work/err"
  local got=$?
  if [ "$got" -eq "$want" ]; then
    ok "$name"
  else
    fail "$name" "exit $got, wanted $want: $(tail -2 "$work/err" | tr '\n' ' ')"
  fi
}

contains() {
  local name="$1" pattern="$2" file="$3"
  if grep -qE -- "$pattern" "$file"; then
    ok "$name"
  else
    fail "$name" "/$pattern/ not found in $(basename "$file")"
  fi
}

report="$work/report.json"

expect "pytest runs the demo project" 0 \
  "$PY" -m pytest fixtures/demo/test_demo.py --testmeta-report "$report"
contains "the report carries the tickets list" '"tickets"' "$report"
contains "the report carries the ticket value" '"DEMO-1"' "$report"
contains "the report carries the call phase" '"call"' "$report"
contains "the report carries the exit status" '"exit_status": 0' "$report"

expect "summary reads the report" 0 $PROGRAM summary "$report"
contains "counts are printed" '^total 2 tests, 1 passed, 0 failed, 1 skipped, 0 error' "$work/out"
contains "the slowest section is printed" '^slowest' "$work/out"
contains "the ticket is shown beside the test" '\[DEMO-1\]' "$work/out"

expect "the duration gate fails on a zero millisecond budget" 1 \
  $PROGRAM summary "$report" --fail-over-ms 0
contains "the gate names its limit" 'gate   over 0 ms' "$work/out"

expect "top limits the slowest list" 0 $PROGRAM summary "$report" --top 1
listed=$(grep -cE '^  +[0-9]+\.[0-9]{3} ms' "$work/out")
if [ "$listed" -eq 1 ]; then ok "exactly one slowest line"; else fail "exactly one slowest line" "$listed"; fi

expect "strict mode refuses an unticketed file" 4 \
  "$PY" -m pytest fixtures/demo --testmeta-strict
contains "the refusal names the tests" 'have no @pytest.mark.ticket marker' "$work/err"

expect "strict mode runs a fully ticketed file" 0 \
  "$PY" -m pytest fixtures/demo/test_demo.py --testmeta-strict

expect "a missing report is exit 2" 2 $PROGRAM summary "$work/absent.json"
contains "the reader says what it could not read" 'cannot read' "$work/err"

printf '{not json' >"$work/broken.json"
expect "a broken report is exit 2" 2 $PROGRAM summary "$work/broken.json"
contains "the reader says it is not JSON" 'is not JSON' "$work/err"

expect "the selftest runs offline" 0 $PROGRAM selftest
contains "the selftest counts its checks" 'checks passed' "$work/out"

expect "--version works without a command" 0 $PROGRAM --version
contains "the version is printed" '0\.1\.0' "$work/out"

printf '\n%d checks, %d failed\n' "$checks" "$failures"
if [ "$failures" -eq 0 ]; then
  printf 'smoke: all checks passed\n'
  exit 0
fi
printf 'smoke: %d check(s) failed\n' "$failures"
exit 1
