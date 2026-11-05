#!/usr/bin/env bash
# End-to-end smoke: drive the queue through its CLI the way a shell would.
set -uo pipefail

PY="${PY:-python}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
WORK="$(mktemp -d)"
DB="$WORK/queue.db"
DB2="$WORK/other.db"
PASSED=0
FAILED=0
trap 'rm -rf "$WORK"' EXIT

ok() { PASSED=$((PASSED + 1)); printf 'ok   %s\n' "$1"; }
fail() { FAILED=$((FAILED + 1)); printf 'FAIL %s\n' "$1"; }

check() {
  local name="$1"
  shift
  if "$@"; then ok "$name"; else fail "$name"; fi
}

check_equal() {
  local name="$1" want="$2" got="$3"
  if [ "$want" = "$got" ]; then ok "$name"; else fail "$name (want '$want', got '$got')"; fi
}

check_match() {
  local name="$1" pattern="$2" file="$3"
  if grep -q -- "$pattern" "$file"; then ok "$name"; else fail "$name (no match for '$pattern')"; fi
}

q() { "$PY" -m "$MODULE" --db "$DB" "$@"; }

# --- push ---------------------------------------------------------------------
JOB="$(q push '{"task": "resize", "n": 3}' 2>"$WORK/err")"
check "push exits 0" test $? -eq 0
check_equal "push prints a 32 character id" 32 "${#JOB}"

q stats >"$WORK/stats" 2>&1
check_match "stats counts a ready job" '^ready=1' "$WORK/stats"

q push 'not json' >/dev/null 2>"$WORK/err"
check_equal "a bad payload exits 2" 2 "$?"
check_match "and says why" 'not JSON' "$WORK/err"

q push '[1, 2]' >/dev/null 2>"$WORK/err2"
check_equal "a non-object payload exits 2" 2 "$?"

printf '{"task": "from file"}' >"$WORK/payload.json"
"$PY" -m "$MODULE" --db "$DB2" push "@$WORK/payload.json" >/dev/null 2>&1
check "push accepts @file (in a queue of its own)" test $? -eq 0

# --- claim --------------------------------------------------------------------
q claim --worker w1 >"$WORK/job.json" 2>"$WORK/err"
check "claim exits 0" test $? -eq 0
check_match "the claim is the job we pushed" "\"id\": \"$JOB\"" "$WORK/job.json"
check_match "the attempt count is one" '\"attempts\": 1' "$WORK/job.json"
check_match "the payload came back" '\"task\": \"resize\"' "$WORK/job.json"

q claim --worker w2 >/dev/null 2>"$WORK/err"
check_equal "a second claim finds nothing (the lease is live)" 1 "$?"
check_match "and says nothing to claim" 'nothing to claim' "$WORK/err"

# --- complete -----------------------------------------------------------------
q complete "$JOB" --worker w1 --result '{"bytes": 128}' >/dev/null 2>&1
check "complete exits 0" test $? -eq 0
q stats >"$WORK/stats2" 2>&1
check_match "the job is done" 'done=1' "$WORK/stats2"
q complete "$JOB" --worker w1 >/dev/null 2>"$WORK/err"
check_equal "completing twice exits 2" 2 "$?"
check_match "the lost lease is explained" 'lease' "$WORK/err"

q list --json >"$WORK/list.json" 2>&1
check "list --json exits 0" test $? -eq 0
check_match "the result is stored" '\"bytes\": 128' "$WORK/list.json"

# --- a job that keeps failing -------------------------------------------------
DEAD_JOB="$(q push '{"task": "explode"}' --max-attempts 1 2>/dev/null)"
q claim --worker w3 >/dev/null 2>&1
q fail "$DEAD_JOB" --worker w3 --error 'ValueError: nope' >"$WORK/state" 2>&1
check_equal "the last attempt is dead and exits 1" 1 "$?"
check_match "and the state is printed" '^dead$' "$WORK/state"
q list --state dead >"$WORK/dead" 2>&1
check_match "the dead letter is listed" "${DEAD_JOB:0:12}" "$WORK/dead"
q claim --worker w3 >/dev/null 2>&1
check_equal "a dead job is never handed out" 1 "$?"

# --- drain --------------------------------------------------------------------
q push '{"task": "one"}' >/dev/null 2>&1
q push '{"task": "two"}' >/dev/null 2>&1
q drain >"$WORK/drain" 2>&1
check "drain exits 0" test $? -eq 0
check_match "drain reports what it did" 'drained 2 done' "$WORK/drain"
q drain --json >"$WORK/drain2" 2>&1
check_match "an empty drain does nothing" '\"claimed\": 0' "$WORK/drain2"

q list --state sold >/dev/null 2>"$WORK/err"
check_equal "an unknown state exits 2" 2 "$?"

# --- the built-in checks ------------------------------------------------------
q selftest >"$WORK/selftest" 2>&1
check_equal "the selftest passes" 0 "$?"
check_match "and reports its count" 'selftest: [0-9]* checks passed, 0 failed' "$WORK/selftest"

q --version >"$WORK/version" 2>&1
check_match "version prints a version" '^'"$PROGRAM"' [0-9]' "$WORK/version"

printf '\n%i passed, %i failed\n' "$PASSED" "$FAILED"
if [ "$FAILED" -ne 0 ]; then
  printf 'smoke: FAILED\n'
  exit 1
fi
printf 'smoke: all checks passed\n'
