#!/usr/bin/env bash
# End-to-end proof: the limiter's answers, its exit codes, and its recovery.
set -uo pipefail

MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
PY="${PY:-python}"

passed=0
failed=0

ok() {
    passed=$((passed + 1))
    printf 'ok   %s\n' "$1"
}

bad() {
    failed=$((failed + 1))
    printf 'FAIL %s\n' "$1"
}

# check NAME EXPECTED_STATUS ACTUAL_STATUS
check() {
    if [ "$2" -eq "$3" ]; then
        ok "$1"
    else
        bad "$1 (wanted exit $2, got $3)"
    fi
}

# contains NAME NEEDLE HAYSTACK
contains() {
    case "$3" in
        *"$2"*) ok "$1" ;;
        *) bad "$1 (missing '$2' in '$3')" ;;
    esac
}

out=$("$PY" -m "$MODULE" --version 2>&1)
status=$?
check "--version exits 0" 0 $status
contains "--version names the program" "$PROGRAM" "$out"

out=$("$PY" -m "$MODULE" check alice 2>&1)
status=$?
check "a single check is allowed" 0 $status
contains "and reports what is left" "remaining=99" "$out"

# Walking into the limit: a burst of three, four asks, the fourth is a denial.
out=$("$PY" -m "$MODULE" check alice --limit 2 --per 1 --capacity 3 --repeat 4 2>&1)
status=$?
check "walking into the limit exits 1" 1 $status
denies=$(printf '%s\n' "$out" | grep -c '^deny ')
check "exactly one request was denied" 1 "$denies"
contains "and the denial carries a wait" "retry_after=0.500s" "$out"

out=$("$PY" -m "$MODULE" check alice --json --limit 1 --per 1 --capacity 1 --repeat 2 2>&1)
contains "json says the retry is one second" '"retry_after_s": 1.0' "$out"

out=$("$PY" -m "$MODULE" simulate --limit 2 --per 1 --capacity 2 --requests 5 --every 100 2>&1)
status=$?
check "simulate exits 0" 0 $status
contains "simulate counts the allowances" "2 of 5 allowed" "$out"
contains "simulate prints a timeline" "t=  0.100s" "$out"

out=$("$PY" -m "$MODULE" demo 2>&1)
status=$?
check "demo exits 0" 0 $status
contains "demo shows the denial" "one too many at once" "$out"
contains "demo shows recovery" "a full bucket again" "$out"
contains "demo prints its counters" "stats " "$out"

err=$("$PY" -m "$MODULE" check alice --limit 0 2>&1 >/dev/null)
status=$?
check "a zero limit exits 2" 2 $status
contains "and says why" "limit must be a positive integer" "$err"

err=$("$PY" -m "$MODULE" check alice --limit 1 --capacity 2 --cost 5 2>&1 >/dev/null)
status=$?
check "a cost above the burst exits 2" 2 $status
contains "and says why" "exceeds the burst" "$err"

err=$("$PY" -m "$MODULE" check "" 2>&1 >/dev/null)
status=$?
check "an empty key exits 2" 2 $status
contains "and says why" "non-empty" "$err"

out=$("$PY" -m "$MODULE" selftest 2>&1)
status=$?
check "selftest exits 0" 0 $status
contains "selftest reports no failures" "0 failed" "$out"

printf '\n%d passed, %d failed\n' "$passed" "$failed"
if [ "$failed" -ne 0 ]; then
    echo "smoke: FAILED"
    exit 1
fi
echo "smoke: all checks passed"
