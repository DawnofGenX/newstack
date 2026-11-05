#!/usr/bin/env bash
# End-to-end checks against the real command line. No test framework needed.
set -uo pipefail

PY="${PY:-python3}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"

PASSED=0
FAILED=0

ok() {
  PASSED=$((PASSED + 1))
  printf 'ok   %s\n' "$1"
}

bad() {
  FAILED=$((FAILED + 1))
  printf 'FAIL %s\n' "$1"
  if [ $# -gt 1 ]; then printf '     %s\n' "$2"; fi
}

run() {
  OUT=$("$@" 2>&1)
  STATUS=$?
}

check() {
  if eval "$2"; then ok "$1"; else bad "$1" "$OUT"; fi
}

check_out() {
  case "$OUT" in
    *"$2"*) ok "$1" ;;
    *) bad "$1" "expected to find: $2" ;;
  esac
}

run "$PY" -m "$MODULE" --version
check "the version banner names the program" '[ "$STATUS" -eq 0 ] && [ "${OUT%% *}" = "$PROGRAM" ]'

run "$PY" -m "$MODULE" demo
check "the demo exits zero" '[ "$STATUS" -eq 0 ]'
check_out "the demo tells the counter story" "a counter merged by max cannot subtract"
check_out "the demo tells the register story" "drops a concurrent write"
check_out "the demo tells the add-wins story" "an observed-remove set keeps the add"
check_out "the demo shows the replicas agreeing" "the replicas agreed"

run "$PY" -m "$MODULE" laws
check "the law report exits zero" '[ "$STATUS" -eq 0 ]'
check_out "the law report says every law held" "laws: all held"
check_out "the law report checks idempotence" "idempotent"
check_out "the law report checks commutativity" "commutative"
check_out "the law report checks associativity" "associative"

run "$PY" -m "$MODULE" selftest
check "the selftest exits zero" '[ "$STATUS" -eq 0 ]'
check_out "the selftest reports its checks" "checks passed"

run "$PY" -m "$MODULE" merge fixtures/counter-a.json fixtures/counter-b.json
check "merging two counters exits zero" '[ "$STATUS" -eq 0 ]'
check_out "the merged counter has node a" '"a": 2'
check_out "the merged counter has node b" '"b": 3'

FIRST=$OUT
run "$PY" -m "$MODULE" merge fixtures/counter-b.json fixtures/counter-a.json
check "the merge is commutative through the cli" '[ "$STATUS" -eq 0 ] && [ "$OUT" = "$FIRST" ]'

run "$PY" -c 'import json, sys; print(json.dumps(json.load(open(sys.argv[1])), indent=2, sort_keys=True))' fixtures/counter-a.json
ALONE=$OUT
run "$PY" -m "$MODULE" merge fixtures/counter-a.json fixtures/counter-a.json
check "merging a state with itself changes nothing" '[ "$OUT" = "$ALONE" ]'

run "$PY" -m "$MODULE" merge fixtures/set-a.json fixtures/set-b.json
check "merging two sets exits zero" '[ "$STATUS" -eq 0 ]'
check_out "both elements survive the merge" '"x"'
check_out "and the second one too" '"y"'

run "$PY" -m "$MODULE" merge fixtures/counter-a.json fixtures/set-a.json
check "merging two different lattices exits two" '[ "$STATUS" -eq 2 ]'
check_out "and says why" "different lattices"

printf '{"type": "signed-total", "counts": {}}\n' > /tmp/crdt-smoke-unknown.json
run "$PY" -m "$MODULE" merge /tmp/crdt-smoke-unknown.json /tmp/crdt-smoke-unknown.json
check "merging a type it does not know exits two" '[ "$STATUS" -eq 2 ]'
rm -f /tmp/crdt-smoke-unknown.json

run "$PY" -m "$MODULE" merge fixtures/counter-a.json fixtures/absent.json
check "a missing file exits two" '[ "$STATUS" -eq 2 ]'

printf '{not json\n' > /tmp/crdt-smoke-broken.json
run "$PY" -m "$MODULE" merge /tmp/crdt-smoke-broken.json fixtures/counter-a.json
check "broken json exits two" '[ "$STATUS" -eq 2 ]'
rm -f /tmp/crdt-smoke-broken.json

run "$PY" -m "$MODULE"
check "no subcommand exits two" '[ "$STATUS" -eq 2 ]'

run "$PY" -m "$MODULE" nonsense
check "an unknown subcommand exits two" '[ "$STATUS" -eq 2 ]'

run "$PY" -m "$MODULE" --help
check "help exits zero" '[ "$STATUS" -eq 0 ]'
check_out "help lists the merge command" "merge"

printf '\n'
printf 'smoke: %s passed, %s failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
