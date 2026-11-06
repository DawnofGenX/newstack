#!/usr/bin/env bash
# Smoke test: run every command the README promises, on the fixture rules.
#
#   PY=.venv/bin/python bash smoke.sh
#
# Uses its own scratch directory under $TMPDIR, so it never touches the project.

set -uo pipefail

PY="${PY:-python3}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/rrule-smoke.XXXXXX")"
PASSED=0
FAILED=0

cleanup() {
  rm -rf "$WORK"
}
trap cleanup EXIT

ok() {
  PASSED=$((PASSED + 1))
  echo "ok   $1"
}

bad() {
  FAILED=$((FAILED + 1))
  echo "FAIL $1${2:+: $2}"
}

check() {
  local name="$1" condition="$2" detail="${3:-}"
  if [ "$condition" = "1" ]; then ok "$name"; else bad "$name" "$detail"; fi
}

check_equal() {
  local name="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    ok "$name"
  else
    bad "$name" "expected '$expected', got '$actual'"
  fi
}

check_contains() {
  local name="$1" needle="$2" haystack="$3"
  case "$haystack" in
    *"$needle"*) ok "$name" ;;
    *) bad "$name" "missing '$needle' in: $haystack" ;;
  esac
}

OUT=""
STATUS=0

run() {
  OUT=$("$@" 2>&1)
  STATUS=$?
}

mod() {
  "$PY" -m "$MODULE" "$@"
}

# --- version and help -------------------------------------------------------
run mod --version
check_equal "version exits zero" "0" "$STATUS"
check_contains "version names the program" "$PROGRAM" "$OUT"

run mod --help
check_equal "help exits zero" "0" "$STATUS"
check_contains "help lists next" "next" "$OUT"
check_contains "help lists explain" "explain" "$OUT"

# --- next -------------------------------------------------------------------
run mod next --rule "FREQ=DAILY" --start "2026-01-01T09:00" --count 3
check_equal "daily next exits zero" "0" "$STATUS"
check_contains "daily next prints the third day" "2026-01-03 09:00" "$OUT"
check_contains "daily next says why it stopped" "limit 3 reached" "$OUT"

run mod next --rule "FREQ=WEEKLY;BYDAY=MO,WE,FR;COUNT=5" --start "2026-01-05T09:00" --zone America/New_York
check_equal "weekly next exits zero" "0" "$STATUS"
check_contains "weekly next reaches the count" "COUNT=5 reached" "$OUT"
check_contains "the fifth firing is the second wednesday" "2026-01-14 09:00" "$OUT"

run mod next --rule "FREQ=DAILY;COUNT=3" --start "2026-03-07T02:30" --zone America/New_York
check_contains "the spring gap is reported" "skipped  2026-03-08 02:30" "$OUT"
check_contains "the gap says the clocks moved" "clocks jumped forward" "$OUT"

run mod next --rule "FREQ=MONTHLY;BYDAY=-1FR;COUNT=2" --start "2026-01-01T17:00" --zone Europe/Berlin
check_contains "the last friday of january" "2026-01-30 17:00" "$OUT"

run mod next --rule "FREQ=YEARLY;COUNT=2" --start "2024-02-29T00:00"
check_contains "a leap day repeats four years later" "2028-02-29 00:00" "$OUT"

# --- json -------------------------------------------------------------------
run mod next --rule "FREQ=DAILY;COUNT=4" --start "2026-03-07T02:30" --zone America/New_York --json
check_equal "json next exits zero" "0" "$STATUS"
COUNT=$("$PY" -c 'import json,sys; print(len(json.loads(sys.argv[1])["occurrences"]))' "$OUT")
check_equal "json next counts four firings" "4" "$COUNT"
INSTANT=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["occurrences"][0]["instant"])' "$OUT")
check_equal "json next maps the wall time to utc" "2026-03-07T07:30:00Z" "$INSTANT"
SKIPPED=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["skipped"][0]["local"])' "$OUT")
check_equal "json next names the skipped wall time" "2026-03-08T02:30:00" "$SKIPPED"

# --- explain ----------------------------------------------------------------
run mod explain --rule "FREQ=WEEKLY;BYDAY=MO" --start "2026-01-05T09:00" --at "2026-01-12T09:00"
check_equal "explain accepts a monday" "0" "$STATUS"
check_contains "explain says it is an occurrence" "an occurrence" "$OUT"

run mod explain --rule "FREQ=WEEKLY;BYDAY=MO" --start "2026-01-05T09:00" --at "2026-01-07T09:00"
check_equal "explain refuses a wednesday" "1" "$STATUS"
check_contains "explain says it is not" "not an occurrence" "$OUT"
check_contains "explain names the weekday" "Wednesday" "$OUT"

run mod explain --rule "FREQ=DAILY" --start "2026-03-06T02:30" --zone America/New_York --at "2026-03-08T02:30"
check_contains "explain knows the gap" "gap the zone made" "$OUT"

# --- between ----------------------------------------------------------------
run mod between --rule "FREQ=DAILY" --start "2026-01-01T09:00" --since "2026-01-03T00:00" --until "2026-01-05T12:00"
check_equal "between exits zero" "0" "$STATUS"
check_contains "between counts three firings" "firings    3" "$OUT"

# --- refusals ---------------------------------------------------------------
run mod between --rule "FREQ=DAILY" --start "2026-01-01T09:00" --since "2026-01-05T00:00" --until "2026-01-03T00:00"
check_equal "an inverted window is unusable" "2" "$STATUS"
check_contains "the window error explains itself" "window is empty" "$OUT"

run mod next --rule "FREQ=DAILY" --start "2026-01-01T09:00+00:00"
check_equal "a start with an offset is unusable" "2" "$STATUS"
check_contains "the offset error names the problem" "wall time" "$OUT"

run mod next --rule "FREQ=DAILY" --start "2026-01-01T09:00" --zone "Mars/Olympus"
check_equal "an unknown zone is unusable" "2" "$STATUS"
check_contains "the zone error names the problem" "not a time zone" "$OUT"

run mod next --rule "FREQ=SOMETIMES" --start "2026-01-01T09:00"
check_equal "an unknown frequency is unusable" "2" "$STATUS"

run mod next --rule "FREQ=YEARLY;BYMONTH=2;BYMONTHDAY=30" --start "2026-01-01T00:00"
check_equal "february 30th is unusable" "2" "$STATUS"
check_contains "the date error says why" "no real date" "$OUT"

run mod next --rule "FREQ=YEARLY;BYMONTH=2;BYMONTHDAY=29" --start "2025-03-01T00:00" --span-years 1
check_equal "a rule that never fires exits one" "1" "$STATUS"
check_contains "and says it never fires" "no occurrence" "$OUT"

# --- fixtures ---------------------------------------------------------------
FIRED=0
ROWS=0
while IFS='|' read -r rule start zone note; do
  case "$rule" in ""|"#"*) continue ;; esac
  ROWS=$((ROWS + 1))
  run mod next --rule "$(echo "$rule" | sed 's/^ *//;s/ *$//')" --start "$(echo "$start" | sed 's/^ *//;s/ *$//')" --zone "$(echo "$zone" | sed 's/^ *//;s/ *$//')" --count 2
  if [ "$STATUS" = "0" ]; then FIRED=$((FIRED + 1)); fi
done < fixtures/rules.txt
check_equal "every fixture rule fires" "$FIRED" "$ROWS"

# --- demo and selftest ------------------------------------------------------
run mod demo
check_equal "demo exits zero" "0" "$STATUS"
check_contains "demo holds every story" "stories      6 of 6 hold" "$OUT"

run mod selftest
check_equal "selftest exits zero" "0" "$STATUS"
check_contains "selftest reports no failures" "0 failed" "$OUT"

# --- summary ----------------------------------------------------------------
echo
if [ "$FAILED" -ne 0 ]; then
  echo "smoke: $FAILED failed, $PASSED passed"
  exit 1
fi
echo "smoke: $PASSED passed, 0 failed"
