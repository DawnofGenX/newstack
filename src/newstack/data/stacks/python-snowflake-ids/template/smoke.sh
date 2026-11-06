#!/usr/bin/env bash
# Smoke test: the command line does what the README says, on a throwaway copy.
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
  printf 'FAIL %s%s\n' "$1" "${2:+: $2}"
}

check_contains() {
  local name="$1" needle="$2" haystack="$3"
  case "$haystack" in
    *"$needle"*) ok "$name" ;;
    *) bad "$name" "expected $needle in: $haystack" ;;
  esac
}

check_status() {
  local name="$1" expected="$2" actual="$3"
  if [ "$actual" -eq "$expected" ]; then
    ok "$name"
  else
    bad "$name" "exit $actual, expected $expected"
  fi
}

run() {
  "$PY" -m "$MODULE" "$@" 2>&1
}

"$PY" -c "import $MODULE" >/dev/null 2>&1
check_status "the package imports" 0 "$?"

out=$(run --version)
check_contains "the version banner names the program" "$PROGRAM " "$out"

out=$(run generate --count 3 --worker 4 --spread)
check_status "generating exits zero" 0 "$?"
check_contains "generating counts the identifiers" "issued       3 identifier(s) from worker 4" "$out"
check_contains "generating reports waits" "waits        0" "$out"
check_contains "each line names the worker" "worker 4" "$out"

out=$(run generate --count 2 --worker 4 --json)
check_status "the json form exits zero" 0 "$?"
check_contains "the json form carries the worker" '"worker": 4' "$out"
check_contains "the json form carries the sequence" '"sequence": 0' "$out"

out=$(run generate --count 4100 --worker 1)
check_status "a one-millisecond burst exits zero" 0 "$?"
check_contains "the burst waits once" "waits        1" "$out"

value=$("$PY" -c "from $MODULE.layout import compose; print(compose(1000, 3, 7))")
out=$(run decode "$value")
check_status "decoding exits zero" 0 "$?"
check_contains "decoding names the worker" "worker 3" "$out"
check_contains "decoding names the sequence" "sequence 7" "$out"

out=$(run capacity)
check_status "capacity exits zero" 0 "$?"
check_contains "capacity names the worker field" "worker       10 bits" "$out"
check_contains "capacity names the end of the layout" "layout ends" "$out"

out=$(run audit --input fixtures/ids.jsonl)
check_status "auditing a clean stream exits zero" 0 "$?"
check_contains "the clean stream is sound" "verdict      sound" "$out"
check_contains "the audit counts the identifiers" "identifiers  12" "$out"

head -n 3 fixtures/ids.jsonl >"$WORK/repeated.jsonl"
head -n 1 fixtures/ids.jsonl >>"$WORK/repeated.jsonl"
out=$(run audit --input "$WORK/repeated.jsonl")
check_status "a duplicate exits one" 1 "$?"
check_contains "the duplicate is named" "1 duplicate(s)" "$out"
check_contains "the verdict is honest" "BROKEN" "$out"

out=$(run audit --input /nonexistent/ids.jsonl)
check_status "a missing file is unusable input" 2 "$?"
check_contains "the refusal names the file" "no such file" "$out"

out=$(run generate --count 1 --worker 2048)
check_status "a worker outside the field is refused" 2 "$?"
check_contains "the refusal names the worker" "worker" "$out"

out=$(run demo)
check_status "the demo exits zero" 0 "$?"
check_contains "every story holds" "stories      6 of 6 hold" "$out"

out=$(run selftest)
check_status "the selftest exits zero" 0 "$?"
check_contains "the selftest reports its checks" "checks passed" "$out"

out=$(run --help)
check_contains "help names the commands" "generate" "$out"

printf 'smoke: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
