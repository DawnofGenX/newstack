#!/usr/bin/env bash
# Smoke test: the command line behaves the way the README says.
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
    *) bad "$name" "expected '$needle' in: $haystack" ;;
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

out=$(run parse "~1.4 || ^2.0")
check_status "parsing a union exits zero" 0 "$?"
check_contains "the union has two arms" "arms       2" "$out"
check_contains "the first arm is printed as an interval" "1. [1.4.0, 1.5.0)" "$out"
check_contains "the second arm is printed as an interval" "2. [2.0.0, 3.0.0)" "$out"

out=$(run satisfy 1.4.2 --range "~1.4 || ^2.0")
check_status "a match exits zero" 0 "$?"
check_contains "the match names the arm" "(arm 1)" "$out"

out=$(run satisfy 1.5.0 --range "~1.4 || ^2.0")
check_status "a miss exits one" 1 "$?"
check_contains "the miss says it does not satisfy" "does not satisfy" "$out"
check_contains "the excluded bound is named" "excluded" "$out"

out=$(run satisfy 1.3.0-beta --range "^1.2.0")
check_status "a prerelease miss exits one" 1 "$?"
check_contains "the prerelease reason is printed" "prerelease" "$out"

out=$(run satisfy 1.3.0-beta --range "^1.2.0" --json)
check_contains "the json form reports false" '"satisfies": false' "$out"

out=$(run satisfy 1.2 --range "*")
check_status "an unreadable version exits two" 2 "$?"
check_contains "the version refusal is printed" "not a version" "$out"

out=$(run satisfy 1.2.3 --range "1.2 || ")
check_status "an unreadable range exits two" 2 "$?"
check_contains "the range refusal is printed" "empty arm" "$out"

out=$(run intersect "^1.2.3" ">=1.4.0 <1.5.0")
check_status "a real overlap exits zero" 0 "$?"
check_contains "the overlap is the tighter interval" "[1.4.0, 1.5.0)" "$out"

out=$(run intersect "^1.0" "^2.0")
check_status "an empty overlap exits one" 1 "$?"
check_contains "the empty verdict is printed" "empty: no version satisfies both" "$out"

out=$(run sort --input fixtures/versions.txt)
check_status "sorting the fixture exits zero" 0 "$?"
check_contains "sorting starts at the lowest version" "0.9.9" "$out"
first=${out%%$'\n'*}
last=${out##*$'\n'}
check_contains "the first line is 0.9.9" "0.9.9" "$first"
check_contains "the last line is 2.0.0" "2.0.0" "$last"

printf '1.2.3\nnope\n' >"$WORK/versions.txt"
out=$(run sort --input "$WORK/versions.txt")
check_status "a bad line exits two" 2 "$?"
check_contains "the bad line is named" "line 2" "$out"

out=$(run sort --input /nonexistent/versions.txt)
check_status "a missing file exits two" 2 "$?"
check_contains "the missing file is named" "no such file" "$out"

out=$(run demo)
check_status "the demo exits zero" 0 "$?"
check_contains "every story holds" "stories      6 of 6 hold" "$out"

out=$(run selftest)
check_status "the selftest exits zero" 0 "$?"
check_contains "the selftest counts its checks" "checks passed" "$out"

out=$(run --help)
check_contains "help names the commands" "intersect" "$out"

printf 'smoke: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
