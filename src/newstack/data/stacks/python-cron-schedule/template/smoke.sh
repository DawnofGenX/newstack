#!/usr/bin/env bash
# Smoke test: the claims that would be embarrassing to get wrong.
set -uo pipefail

MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
PY="${PY:-.venv/bin/python}"

passed=0
failed=0

ok() {
  passed=$((passed + 1))
  printf '  ok   %s\n' "$1"
}

bad() {
  failed=$((failed + 1))
  printf '  FAIL %s\n' "$1"
  [ $# -gt 1 ] && printf '       %s\n' "$2"
}

rr() {
  "$@" >/tmp/smoke-out 2>/tmp/smoke-err
  return $?
}

want_status() {
  local name="$1" want="$2" got="$3"
  if [ "$want" = "$got" ]; then
    ok "$name (exit $got)"
  else
    bad "$name" "wanted exit $want, got $got: $(head -2 /tmp/smoke-err)"
  fi
}

grep_out() {
  local name="$1" pattern="$2"
  if grep -q -- "$pattern" /tmp/smoke-out; then
    ok "$name"
  else
    bad "$name" "output did not contain: $pattern"
  fi
}

grep_err() {
  local name="$1" pattern="$2"
  if grep -q -- "$pattern" /tmp/smoke-err; then
    ok "$name"
  else
    bad "$name" "stderr did not contain: $pattern"
  fi
}

echo "smoke: $PROGRAM on $(python3 -c 'import sys; print(sys.version.split()[0])')"

# 1. the banner names the program and the version
rr "$PY" -m "$MODULE" --version
want_status "version runs" 0 $?
if grep -q "^$PROGRAM 0\.1\.0$" /tmp/smoke-out; then
  ok "the banner names the program"
else
  bad "the banner names the program" "$(cat /tmp/smoke-out)"
fi

# 2. an ordinary schedule, counted
rr "$PY" -m "$MODULE" next "*/15 * * * *" --after 2026-03-07T12:04:30Z --count 3
want_status "every fifteen minutes" 0 $?
grep_out "the first run is 12:15" "2026-03-07T12:15:00Z"
grep_out "the third run is 12:45" "2026-03-07T12:45:00Z"

# 3. the hour that does not exist
rr "$PY" -m "$MODULE" next "30 2 * * *" --after 2026-03-07T12:00:00Z --tz America/New_York
want_status "spring forward" 0 $?
grep_out "02:30 skips to the next day" "2026-03-09T06:30:00Z"

# 4. the hour that happens twice
rr "$PY" -m "$MODULE" next "30 1 * * *" --after 2026-10-31T12:00:00Z --tz America/New_York --count 3
want_status "fall back" 0 $?
grep_out "01:30 EDT runs first" "2026-11-01T05:30:00Z"
grep_out "01:30 EST runs again" "2026-11-01T06:30:00Z"

# 5. the day rule
rr "$PY" -m "$MODULE" explain "0 0 1 * 1"
want_status "explain" 0 $?
grep_out "two restricted day fields are joined with OR" "day rule   or"
rr "$PY" -m "$MODULE" explain "0 9 * * mon-fri"
grep_out "one restricted day field is joined with AND" "day rule   and"

# 6. json is json
rr "$PY" -m "$MODULE" next "0 0 1 * *" --after 2026-03-02T00:00:00Z --json
want_status "json" 0 $?
if "$PY" -c 'import json,sys; json.load(open("/tmp/smoke-out"))["runs"][0]["utc"]' >/dev/null 2>&1; then
  ok "the json parses and carries the instants"
else
  bad "the json parses and carries the instants"
fi

# 7. refusals
rr "$PY" -m "$MODULE" next "*/0 * * * *"
want_status "a step of zero is refused" 2 $?
grep_err "and says what is wrong" "step must be at least 1"
rr "$PY" -m "$MODULE" next "* * * * *" --after 2026-03-02T00:00:00
want_status "a moment with no offset is refused" 2 $?
grep_err "and says why that matters" "has no offset"
rr "$PY" -m "$MODULE" next "* * * * *" --tz Mars/Olympus
want_status "an unknown zone is refused" 2 $?
grep_err "and names the zone" "unknown time zone"
rr "$PY" -m "$MODULE" next "* * * *"
want_status "four fields are not a schedule" 2 $?
grep_err "and counts them" "five fields"

# 8. a valid schedule that never fires
rr "$PY" -m "$MODULE" next "0 0 30 2 *" --after 2026-03-02T00:00:00Z
want_status "February 30 has no run" 1 $?
grep_err "and says the window was searched" "describes nothing"

# 9. the demo and the selftest
rr "$PY" -m "$MODULE" demo
want_status "demo" 0 $?
grep_out "every scenario is as advertised" "demo: 6 schedules, 0 not as advertised"
rr "$PY" -m "$MODULE" selftest
want_status "selftest" 0 $?
grep_out "no check failed" "0 failed"

printf '\nsmoke: %s passed, %s failed\n' "$passed" "$failed"
if [ "$failed" -eq 0 ]; then
  echo "smoke: all checks passed"
  exit 0
fi
exit 1
