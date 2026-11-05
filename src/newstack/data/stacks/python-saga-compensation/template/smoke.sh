#!/usr/bin/env bash
# Smoke-test a freshly generated saga project: the rules that matter, end to end.
set -uo pipefail

PY=${PY:-python}
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

passed=0
failed=0
ok()   { printf 'ok    %s\n' "$1"; passed=$((passed + 1)); }
bad()  { printf 'FAIL  %s\n' "$1"; failed=$((failed + 1)); }
check_equal() {
  local name=$1 want=$2 got=$3
  if [ "$want" = "$got" ]; then ok "$name"; else bad "$name (wanted '$want', got '$got')"; fi
}
check_contains() {
  local name=$1 needle=$2 haystack=$3
  case $haystack in
    *"$needle"*) ok "$name" ;;
    *) bad "$name (wanted '$needle')" ;;
  esac
}
run() {
  local cmd=$1
  shift
  output=$("$cmd" "$@" 2>&1)
  status=$?
}

run "$PY" -m "$MODULE" --version
check_contains "the version banner names the program" "$PROGRAM " "$output"

run "$PY" -m "$MODULE" --help
check_contains "help lists the run command" "run" "$output"

JOURNAL="$WORK/happy.jsonl"
run "$PY" -m "$MODULE" run --journal "$JOURNAL" --decline ""
check_equal "a clean run exits 0" 0 "$status"
check_contains "a clean run completes" "status     completed" "$output"

DECLINED="$WORK/declined.jsonl"
run "$PY" -m "$MODULE" run --journal "$DECLINED"
check_equal "a declined run exits 1" 1 "$status"
check_contains "the rollback is reported" "status     rolled_back" "$output"
check_contains "the compensations ran backwards" \
  "reserve-hotel -> charge-card -> book-flight -> refund-card -> release-hotel" "$output"
check_contains "the failed step is named" "failed     book-flight" "$output"

STUCK="$WORK/stuck.jsonl"
run "$PY" -m "$MODULE" run --journal "$STUCK" --break-compensation charge-card
check_equal "an incomplete rollback exits 2" 2 "$status"
check_contains "the incomplete rollback is named" "status     incomplete" "$output"
check_contains "what is left standing is printed" "left       charge-card" "$output"
check_contains "the other compensation still ran" "reserve-hotel        compensated" "$output"

run "$PY" -m "$MODULE" journal --journal "$STUCK" --json
check_equal "the journal command exits 2 for an incomplete saga" 2 "$status"
check_contains "the journal reports the outcome" '"outcome": "incomplete"' "$output"
check_contains "the journal reports the failed compensation" '"compensation_failed"' "$output"

run "$PY" -m "$MODULE" journal --journal "$WORK/none.jsonl"
check_equal "a missing journal exits 3" 3 "$status"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits 0" 0 "$status"
check_contains "the selftest reports passes" "checks passed" "$output"

run "$PY" -m "$MODULE" demo
check_equal "the demo exits 2 (its worst scenario is incomplete)" 2 "$status"
check_contains "the demo shows a rollback" "status     rolled_back" "$output"
check_contains "the demo shows an incomplete rollback" "status     incomplete" "$output"

# The journal is append-only: running the same saga twice does not duplicate history.
before=$(wc -l <"$DECLINED")
run "$PY" -m "$MODULE" run --journal "$DECLINED"
after=$(wc -l <"$DECLINED")
check_equal "a finished saga does not touch the journal again" "$before" "$after"
check_contains "the re-run says it resumed" "resumed    yes" "$output"

if [ "$failed" -ne 0 ]; then
  printf 'smoke: %d passed, %d failed\n' "$passed" "$failed"
  exit 1
fi
printf 'smoke: %d passed, 0 failed\n' "$passed"
