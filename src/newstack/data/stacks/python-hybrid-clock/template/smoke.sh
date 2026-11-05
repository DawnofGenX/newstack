#!/usr/bin/env bash
# Smoke test for the generated project: the README's claims, checked from the
# outside, with the exit codes a caller would actually branch on.
set -uo pipefail

MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PY:-${ROOT}/.venv/bin/python}"

passed=0
failed=0

ok() {
    passed=$((passed + 1))
    printf 'ok   %s\n' "$1"
}

bad() {
    failed=$((failed + 1))
    printf 'FAIL %s\n' "$1"
    if [ -n "${2:-}" ]; then printf '       %s\n' "$2"; fi
}

check() {
    local name="$1"
    shift
    if "$@" >/dev/null 2>&1; then ok "$name"; else bad "$name" "exited non-zero"; fi
}

check_status() {
    local name="$1" want="$2" got="$3"
    if [ "$got" -eq "$want" ]; then
        ok "$name"
    else
        bad "$name" "exit $got, wanted $want"
    fi
}

check_equal() {
    local name="$1" want="$2" got="$3"
    if [ "$want" = "$got" ]; then ok "$name"; else bad "$name" "got '$got', wanted '$want'"; fi
}

check_contains() {
    local name="$1" needle="$2" file="$3"
    if grep -Fq -- "$needle" "$file"; then ok "$name"; else bad "$name" "missing '$needle'"; fi
}

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

"$PY" -m "$MODULE" demo >"$WORK/demo.txt" 2>&1
check_status "demo exits zero" 0 "$?"
check_contains "the demo holds its stories" "-> holds" "$WORK/demo.txt"
check_equal "every story is present" 6 "$(grep -Fc -- "-> holds" "$WORK/demo.txt")"
check_contains "the wall step back keeps the stamps increasing" \
    "the stamps still increase: True" "$WORK/demo.txt"
check_contains "the skew refusal names the bound" "past the 400 ms bound" "$WORK/demo.txt"
if grep -Fq -- "BROKEN" "$WORK/demo.txt"; then
    bad "no story is broken" "the demo printed BROKEN"
else
    ok "no story is broken"
fi

"$PY" -m "$MODULE" plan --plan fixtures/handoff.jsonl >"$WORK/plan.txt" 2>&1
check_status "a plan exits zero" 0 "$?"
check_contains "the plan counts its messages" "messages     1" "$WORK/plan.txt"
check_contains "the plan reports no causal break" "causal breaks 0" "$WORK/plan.txt"
check_contains "the report names the columns" "physical_ms" "$WORK/plan.txt"

"$PY" -m "$MODULE" plan --plan fixtures/step-back.jsonl >"$WORK/back.txt" 2>&1
check_status "a plan whose wall steps back exits zero" 0 "$?"
check_contains "the step-back plan breaks no causality" "causal breaks 0" "$WORK/back.txt"

"$PY" -m "$MODULE" plan --plan fixtures/handoff.jsonl --max-skew 100 >"$WORK/skew.txt" 2>&1
check_status "a skew past the bound exits one" 1 "$?"
check_contains "the skew refusal is printed" "past the 100 ms bound" "$WORK/skew.txt"

"$PY" -m "$MODULE" plan --plan fixtures/handoff.jsonl --json >"$WORK/plan.json" 2>&1
check_status "the json plan exits zero" 0 "$?"
check "the json carries one message and no violation" "$PY" -c \
    'import json,sys; d=json.load(open(sys.argv[1])); assert d["messages"]==1, d;
assert d["violations"]==[], d' "$WORK/plan.json"

"$PY" -m "$MODULE" plan --plan /nonexistent/plan.jsonl >"$WORK/missing.txt" 2>&1
check_status "a missing plan file exits two" 2 "$?"
check_contains "a missing plan explains itself" "error:" "$WORK/missing.txt"

"$PY" -m "$MODULE" stamp 000001700000000000:0000003@a >"$WORK/stamp.txt" 2>&1
check_status "a stamp reads back" 0 "$?"
check_contains "the stamp prints its key" "(1700000000000, 3, 'a')" "$WORK/stamp.txt"

"$PY" -m "$MODULE" stamp "not a stamp" >"$WORK/bad.txt" 2>&1
check_status "a broken stamp exits two" 2 "$?"
check_contains "a broken stamp says what shape it wants" "<physical_ms>" "$WORK/bad.txt"

"$PY" -m "$MODULE" --version >"$WORK/version.txt" 2>&1
check_status "the version banner exits zero" 0 "$?"
check_contains "the banner names the program" "$PROGRAM 0.1.0" "$WORK/version.txt"

"$PY" -m "$MODULE" --help >"$WORK/help.txt" 2>&1
check_status "help exits zero" 0 "$?"
check_contains "help lists the plan command" "plan" "$WORK/help.txt"
check_contains "help lists the selftest command" "selftest" "$WORK/help.txt"

"$PY" -m "$MODULE" selftest >"$WORK/selftest.txt" 2>&1
check_status "selftest exits zero" 0 "$?"
check_contains "selftest reports its checks" "checks passed" "$WORK/selftest.txt"

printf '\nsmoke: %d passed, %d failed\n' "$passed" "$failed"
if [ "$failed" -ne 0 ]; then exit 1; fi
