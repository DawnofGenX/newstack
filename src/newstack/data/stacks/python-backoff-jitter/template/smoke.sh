#!/usr/bin/env bash
# Smoke test: the CLI must answer the same way a reader would.
set -uo pipefail

PY="${PY:-.venv/bin/python}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"

passed=0
failed=0

ok() {
  passed=$((passed + 1))
  printf '  ok   %s\n' "$1"
}

bad() {
  failed=$((failed + 1))
  printf '  FAIL %s\n' "$1"
}

check() {
  if [ "$2" = "$3" ]; then ok "$1"; else bad "$1 (expected '$3', got '$2')"; fi
}

check_contains() {
  case "$2" in
    *"$3"*) ok "$1" ;;
    *) bad "$1 (missing '$3')" ;;
  esac
}

check_missing() {
  case "$2" in
    *"$3"*) bad "$1 (found '$3')" ;;
    *) ok "$1" ;;
  esac
}

echo "smoke: $PROGRAM"

out=$("$PY" -m "$MODULE" --version 2>&1)
check_contains "version names the program" "$out" "$PROGRAM"

out=$("$PY" -m "$MODULE" --help 2>&1)
check_contains "help lists simulate" "$out" "simulate"
check_contains "help lists compare" "$out" "compare"

out=$("$PY" -m "$MODULE" simulate --policy fixed --clients 40 2>&1)
status=$?
check "a plain run exits zero" "$status" "0"
check_contains "a plain run names the policy" "$out" "fixed"
check_contains "a plain run reports the peak" "$out" "peak"

out=$("$PY" -m "$MODULE" simulate --policy exponential --clients 40 --bucket-ms 0 2>&1)
status=$?
check "a zero bucket is unusable" "$status" "2"
check_contains "the refusal explains itself" "$out" "bucket_ms"

out=$("$PY" -m "$MODULE" simulate --policy nosuch 2>&1)
status=$?
check "an unknown policy is unusable" "$status" "2"
check_contains "the refusal lists the known policies" "$out" "full-jitter"

out=$("$PY" -m "$MODULE" simulate --policy fixed --clients 40 --max-peak 5 2>&1)
status=$?
check "a breached peak exits one" "$status" "1"
check_contains "the gate line says BREACH" "$out" "BREACH"

out=$("$PY" -m "$MODULE" simulate --policy full-jitter --clients 200 --max-peak 60 2>&1)
status=$?
check "a held peak exits zero" "$status" "0"
check_contains "the gate line says ok" "$out" "ok"

out=$("$PY" -m "$MODULE" simulate --policy fixed --clients 30 --json 2>&1)
check_contains "json reports the peak" "$out" '"peak_retries": 30'
check_contains "json names the policy" "$out" '"policy"'

out=$("$PY" -m "$MODULE" compare --clients 40 2>&1)
status=$?
check "compare exits zero" "$status" "0"
check_contains "compare prints five policies" "$out" "decorrelated"
check_contains "compare compares the pile-up" "$out" "pile-up"

out=$("$PY" -m "$MODULE" demo 2>&1)
status=$?
check "the demo exits zero" "$status" "0"
check_contains "the demo holds every story" "$out" "-> holds"
check_missing "the demo claims nothing broken" "$out" "BROKEN"

out=$("$PY" -m "$MODULE" selftest 2>&1)
status=$?
check "selftest exits zero" "$status" "0"
check_contains "selftest reports its checks" "$out" "checks passed"

out=$("$PY" -c "from $MODULE.simulate import simulate; from $MODULE.policies import Fixed; r = simulate(Fixed(100.0), clients=20, seed=3, fail_ms=300.0); print(r.peak_retries, r.completed)" 2>&1)
check "the library settles every client" "$out" "20 True"

echo
if [ "$failed" -ne 0 ]; then
  echo "smoke: $failed failed, $passed passed"
  exit 1
fi
echo "smoke: $passed passed, 0 failed"
