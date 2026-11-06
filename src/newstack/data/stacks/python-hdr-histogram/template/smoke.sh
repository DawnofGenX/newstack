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

out=$(run percentile --input fixtures/latencies.jsonl --p 50,90,99)
check_status "a percentile run exits zero" 0 "$?"
check_contains "the run reports the sample count" "240 sample(s)" "$out"
check_contains "the run names the promise" "promised" "$out"
check_contains "the run compares against the truth" "reported" "$out"
check_contains "the run reaches a verdict" "within the promise" "$out"

out=$(run percentile --input fixtures/latencies.jsonl --p 50,99 --json)
check_status "the json form exits zero" 0 "$?"
check_contains "the json form carries the promise" '"promised"' "$out"
check_contains "the json form carries the verdict" '"held": true' "$out"

out=$(run record --input fixtures/latencies.jsonl --out "$WORK/histogram.json")
check_status "recording exits zero" 0 "$?"
check_contains "recording counts every sample" "samples      240" "$out"
check_contains "the histogram file is written" "histogram.json" "$out"

out=$(run info --histogram "$WORK/histogram.json")
check_status "info exits zero" 0 "$?"
check_contains "info names the percentile" "p99" "$out"
check_contains "info names the resolution" "bits" "$out"

head -n 125 fixtures/latencies.jsonl >"$WORK/first.jsonl"
tail -n 115 fixtures/latencies.jsonl >"$WORK/second.jsonl"
run record --input "$WORK/first.jsonl" --out "$WORK/first.json" >/dev/null
run record --input "$WORK/second.jsonl" --out "$WORK/second.json" >/dev/null
out=$(run merge --left "$WORK/first.json" --right "$WORK/second.json" --out "$WORK/merged.json")
check_status "merging two halves exits zero" 0 "$?"
check_contains "the merge counts both halves" "merged       240 sample(s)" "$out"

out=$(run percentile --input /nonexistent/latencies.jsonl)
check_status "a missing file is a usage error" 2 "$?"
check_contains "the usage error names the file" "no such file" "$out"

: >"$WORK/empty.jsonl"
out=$(run percentile --input "$WORK/empty.jsonl")
check_status "an empty input is refused" 2 "$?"
check_contains "the refusal explains itself" "no latencies" "$out"

out=$(run percentile --input fixtures/latencies.jsonl --p fifty)
check_status "an unreadable percentile is refused" 2 "$?"
check_contains "the refusal names the percentile" "not a percentile" "$out"

printf '{"type": "count-min-sketch"}\n' >"$WORK/foreign.json"
out=$(run info --histogram "$WORK/foreign.json")
check_status "a foreign document is refused" 2 "$?"
check_contains "the refusal names the type" "not a histogram" "$out"

out=$(run demo)
check_status "the demo exits zero" 0 "$?"
check_contains "every story holds" "stories      6 of 6 hold" "$out"

out=$(run selftest)
check_status "the selftest exits zero" 0 "$?"
check_contains "the selftest reports its checks" "checks passed" "$out"

out=$(run --help)
check_contains "help names the commands" "percentile" "$out"

printf 'smoke: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
