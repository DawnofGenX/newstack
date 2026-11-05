#!/usr/bin/env bash
# Proves the claims in README.md against the built package, with real threads.
set -uo pipefail

PY="${PY:-python}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

passed=0
failed=0
ok() { passed=$((passed + 1)); printf 'ok    %s\n' "$1"; }
bad() { failed=$((failed + 1)); printf 'FAIL  %s\n' "$1"; }
contains() {
  local name="$1" haystack="$2" needle="$3"
  case "$haystack" in
    *"$needle"*) ok "$name" ;;
    *) bad "$name (wanted '$needle' in the output)" ;;
  esac
}
run() { "$@" >"$WORK/out" 2>"$WORK/err"; status=$?; }

run "$PY" -m "$MODULE" --version
contains "the version banner names the program" "$(cat "$WORK/out")" "$PROGRAM 0.1.0"

run "$PY" -m "$MODULE" run --callers 40 --delay 0.08
out="$(cat "$WORK/out")"
[ "$status" -eq 0 ] && ok "a clean burst exits 0" || bad "a clean burst exits 0 (got $status)"
contains "forty callers cause one load" "$out" "1 load(s)"
contains "the waiters are counted" "$out" "39 waited"
contains "everybody saw one value" "$out" "values   1 distinct"
contains "the sequential cost is named" "$out" "3200 ms"

run "$PY" -m "$MODULE" run --callers 10 --delay 0.02 --json
out="$(cat "$WORK/out")"
contains "json reports one load" "$out" '"loads": 1'
contains "json reports nine waiters" "$out" '"waits": 9'
contains "json counts the calls" "$out" '"calls": 10'

run "$PY" -m "$MODULE" run --callers 1 --delay 0.01
contains "a single caller is a load, not a hit" "$(cat "$WORK/out")" "0 waited"

run "$PY" -m "$MODULE" run --callers 2 --delay 0 --ttl 0
[ "$status" -eq 2 ] && ok "a zero ttl exits 2" || bad "a zero ttl exits 2 (got $status)"
contains "the refusal explains itself" "$(cat "$WORK/err")" "ttl must be positive"

run "$PY" -m "$MODULE" demo
out="$(cat "$WORK/out")"
[ "$status" -eq 0 ] && ok "demo exits 0" || bad "demo exits 0 (got $status)"
contains "the stampede scenario holds" "$out" "thirty callers, one slow loader"
contains "the failure scenario holds" "$out" "a failed load is remembered for nobody"
contains "the ttl scenario holds" "$out" "a TTL starts when the value became readable"
contains "nothing was missed" "$out" "demo: 4 scenarios, 0 not as advertised"

run "$PY" -m "$MODULE" selftest
out="$(cat "$WORK/out")"
[ "$status" -eq 0 ] && ok "selftest exits 0" || bad "selftest exits 0 (got $status)"
contains "the selftest reports no failures" "$out" "0 failed"

run "$PY" -m "$MODULE" --help
contains "the help names the run command" "$(cat "$WORK/out")" "run"

printf '\n%d passed, %d failed\n' "$passed" "$failed"
if [ "$failed" -ne 0 ]; then
  echo "smoke: FAILED"
  exit 1
fi
echo "smoke: all checks passed"
