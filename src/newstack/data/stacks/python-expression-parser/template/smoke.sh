#!/usr/bin/env bash
# End-to-end checks against the installed command, not the modules.
#
#   PY=.venv/bin/python bash smoke.sh
set -uo pipefail

PY="${PY:-python3}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

PASS=0
FAILS=0

ok() {
    PASS=$((PASS + 1))
    printf 'ok   %s\n' "$1"
}

bad() {
    FAILS=$((FAILS + 1))
    printf 'FAIL %s\n' "$1"
}

check_equal() {
    if [ "$2" = "$3" ]; then
        ok "$1"
    else
        bad "$1 (expected '$2', got '$3')"
    fi
}

check_contains() {
    case "$3" in
        *"$2"*) ok "$1" ;;
        *) bad "$1 (missing '$2' in: ${3:0:200})" ;;
    esac
}

run() {
    OUT="$("$@" 2>&1)"
    STATUS=$?
}

# --- the command answers at all ---------------------------------------------
run "$PY" -m "$MODULE" --version
check_equal "version exits zero" 0 "$STATUS"
check_contains "version names the program" "$PROGRAM" "$OUT"

run "$PY" -m "$MODULE" --help
check_equal "help exits zero" 0 "$STATUS"
check_contains "help lists eval" "eval" "$OUT"
check_contains "help lists explain" "explain" "$OUT"

# --- arithmetic that the obvious implementation gets wrong ------------------
run "$PY" -m "$MODULE" eval "2 + 3 * 4"
check_equal "precedence exits zero" 0 "$STATUS"
check_contains "multiplication binds first" "value      14" "$OUT"

run "$PY" -m "$MODULE" eval "(2 + 3) * 4"
check_contains "parentheses change the answer" "value      20" "$OUT"

run "$PY" -m "$MODULE" eval "2 ^ 3 ^ 2"
check_contains "the power is right-associative" "value      512" "$OUT"

run "$PY" -m "$MODULE" eval "-2 ^ 2"
check_contains "a power binds tighter than unary minus" "value      -4" "$OUT"

# --- exactness ---------------------------------------------------------------
run "$PY" -m "$MODULE" eval "0.1 + 0.2"
check_contains "decimals are exact" "value      0.3" "$OUT"
check_contains "exact mode is named" "mode       exact" "$OUT"

run "$PY" -m "$MODULE" eval "1 / 8"
check_contains "an eighth terminates" "value      0.125" "$OUT"

run "$PY" -m "$MODULE" eval "1 / 3"
check_equal "a third is refused" 1 "$STATUS"
check_contains "and says why" "no finite decimal expansion" "$OUT"

run "$PY" -m "$MODULE" eval "1 / 3" --inexact
check_equal "a third rounds when asked" 0 "$STATUS"
check_contains "the rounding is printed" "0.3333333333333333333333333333" "$OUT"
check_contains "the precision is stated" "rounded to 28 digits" "$OUT"

run "$PY" -m "$MODULE" eval "1 / 0"
check_equal "division by zero is refused" 1 "$STATUS"
check_contains "and names the operation" "division by zero" "$OUT"

# --- variables ---------------------------------------------------------------
run "$PY" -m "$MODULE" eval "x * 2" --var x=21
check_contains "a variable is substituted" "value      42" "$OUT"

run "$PY" -m "$MODULE" eval "x" --var x
check_equal "a malformed --var is unusable" 2 "$STATUS"
check_contains "and says the shape it wants" "name=value" "$OUT"

run "$PY" -m "$MODULE" eval "y + 1"
check_equal "an undefined name is refused" 1 "$STATUS"
check_contains "and is named" "not defined" "$OUT"

# --- the tree ---------------------------------------------------------------
run "$PY" -m "$MODULE" parse "2 + 3 * 4"
check_equal "parse exits zero" 0 "$STATUS"
check_contains "parse prints the canonical text" "render     2 + 3 * 4" "$OUT"
check_contains "parse prints the tree" "    *   multiplicative, column 7" "$OUT"

run "$PY" -m "$MODULE" parse "(2 * 3) + 4"
check_contains "a redundant parenthesis is dropped" "render     2 * 3 + 4" "$OUT"

run "$PY" -m "$MODULE" parse "2 * (3 + 4)"
check_contains "a needed parenthesis is kept" "render     2 * (3 + 4)" "$OUT"

run "$PY" -m "$MODULE" parse "2 * 3" --json
check_equal "parse --json exits zero" 0 "$STATUS"
run "$PY" -c "import json,sys; d=json.loads(sys.argv[1]); print(d['tree']['op'], d['depth'])" "$OUT"
check_equal "the payload carries the shape" "* 2" "$OUT"

# --- errors name their column ----------------------------------------------
run "$PY" -m "$MODULE" eval "2 + * 3"
check_equal "a stray operator is unusable" 2 "$STATUS"
check_contains "the column is named" "column 5" "$OUT"
check_contains "a caret is drawn" "^" "$OUT"

run "$PY" -m "$MODULE" eval "1 + (2"
check_equal "an unclosed group is unusable" 2 "$STATUS"
check_contains "the opening column is named" "opened at column 5" "$OUT"

run "$PY" -m "$MODULE" eval "1 < 2 < 3"
check_contains "a chained comparison is refused" "chain" "$OUT"

# --- explain, demo, selftest ------------------------------------------------
run "$PY" -m "$MODULE" explain "2 + 3 * 4"
check_equal "explain exits zero" 0 "$STATUS"
check_contains "explain prints the table" "precedence" "$OUT"
check_contains "explain prints the value" "value      14" "$OUT"

run "$PY" -m "$MODULE" demo
check_equal "demo exits zero" 0 "$STATUS"
check_contains "every story holds" "stories      6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "selftest exits zero" 0 "$STATUS"
check_contains "selftest reports no failures" "0 failed" "$OUT"

printf '\nsmoke: %d passed, %d failed\n' "$PASS" "$FAILS"
[ "$FAILS" -eq 0 ]
