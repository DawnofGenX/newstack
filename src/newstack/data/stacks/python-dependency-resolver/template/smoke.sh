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

check_equal() {
  if [ "$2" = "$3" ]; then ok "$1"; else bad "$1" "expected [$3] got [$2]"; fi
}

check_contains() {
  case "$2" in
    *"$3"*) ok "$1" ;;
    *) bad "$1" "expected to find [$3] in [$2]" ;;
  esac
}

run() {
  OUTPUT=$("$@" 2>/tmp/smoke-err.$$)
  STATUS=$?
  ERR=$(cat /tmp/smoke-err.$$)
  rm -f /tmp/smoke-err.$$
}

printf 'smoke: %s\n' "$PROGRAM"

run "$PY" -m "$MODULE" --version
check_equal "the banner names the program" "${OUTPUT%% *}" "$PROGRAM"
check_equal "and exits zero" "$STATUS" 0

run "$PY" -m "$MODULE" --help
check_equal "help exits zero" "$STATUS" 0
check_contains "help lists resolve" "$OUTPUT" "resolve"

run "$PY" -m "$MODULE" resolve --root web=^2.0.0 --root cli=^1.0.0
check_equal "the diamond resolves" "$STATUS" 0
check_contains "and abandons the greedy web" "$OUTPUT" "web                2.0.0"
check_contains "and reports its package count" "$OUTPUT" "resolved 3 package(s)"

run "$PY" -m "$MODULE" resolve --root shared=^2.0.0
check_contains "a stable range does not take a release candidate" "$OUTPUT" "shared             2.0.0"

run "$PY" -m "$MODULE" resolve --root tiny=^0.2.0
check_contains "a caret at zero stays on the minor" "$OUTPUT" "tiny               0.2.3"

run "$PY" -m "$MODULE" resolve --root web=^2.1.0 --root cli=^1.0.0
check_equal "a conflict exits one" "$STATUS" 1
check_equal "and prints no tree" "$OUTPUT" ""
check_contains "and explains itself" "$ERR" "no resolution exists"
check_contains "and names the shared package" "$ERR" "shared"

run "$PY" -m "$MODULE" resolve --root web=banana
check_equal "an unreadable range exits two" "$STATUS" 2
check_contains "and quotes the text" "$ERR" "banana"

run "$PY" -m "$MODULE" resolve --root web
check_equal "a malformed root exits two" "$STATUS" 2
check_contains "and shows the shape" "$ERR" "name=RANGE"

run "$PY" -m "$MODULE" resolve --root web=^2.0.0 --root web=^2.1.0
check_equal "a repeated root exits two" "$STATUS" 2

run "$PY" -m "$MODULE" resolve
check_equal "no root at all exits two" "$STATUS" 2

run "$PY" -m "$MODULE" why --root web=^2.0.0 --root cli=^1.0.0 shared
check_equal "why exits zero" "$STATUS" 0
check_contains "and names the first parent" "$OUTPUT" "web@2.0.0 needs shared ^1.2.0"
check_contains "and the second parent" "$OUTPUT" "cli@1.1.0 needs shared ^1.0.0"

run "$PY" -m "$MODULE" why --root web=^2.0.0 tiny
check_equal "why refuses a package that is not there" "$STATUS" 2

LOCK="/tmp/smoke-lock.$$.json"
rm -f "$LOCK"
run "$PY" -m "$MODULE" resolve --root web=^2.0.0 --root cli=^1.0.0 --write-lock "$LOCK"
check_equal "writing a lock exits zero" "$STATUS" 0
if [ -f "$LOCK" ]; then ok "the lockfile exists"; else bad "the lockfile exists"; fi
check_contains "the lockfile records its format" "$(cat "$LOCK" 2>/dev/null)" '"version": 1'
check_contains "the lockfile pins web" "$(cat "$LOCK" 2>/dev/null)" '"web": "2.0.0"'

run "$PY" -m "$MODULE" check --root web=^2.0.0 --root cli=^1.0.0 --lock "$LOCK"
check_equal "a current lock exits zero" "$STATUS" 0
check_contains "and says so" "$OUTPUT" "still resolves"

run "$PY" -m "$MODULE" check --root shared=^2.0.0 --lock "$LOCK"
check_equal "a stale lock exits one" "$STATUS" 1
check_contains "and counts the drift" "$OUTPUT" "drift(s)"

run "$PY" -m "$MODULE" check --root web=^2.0.0 --lock /tmp/absent-lock.$$.json
check_equal "a missing lock exits two" "$STATUS" 2
rm -f "$LOCK"

run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" "$STATUS" 0
check_contains "and reaches the sixth story" "$OUTPUT" "6. a lock keeps the tree"
check_contains "and shows the backtracking answer" "$OUTPUT" "web 2.0.0"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" "$STATUS" 0
check_contains "and reports its checks" "$OUTPUT" "checks passed"

run "$PY" -m "$MODULE" nothing-like-this
check_equal "an unknown subcommand exits two" "$STATUS" 2

printf '\nsmoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
