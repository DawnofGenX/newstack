#!/usr/bin/env bash
# Real runs of the CLI. Every assertion here is something a user can see.
set -uo pipefail

PY="${PY:-.venv/bin/python}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
cd "$(dirname "$0")" || exit 1

passed=0
failed=0
ok() { printf '  ok    %s\n' "$1"; passed=$((passed + 1)); }
bad() { printf '  FAIL  %s\n' "$1"; failed=$((failed + 1)); [ -n "${2:-}" ] && printf '        %s\n' "$2"; }
check() { if [ "$1" = "0" ]; then ok "$2"; else bad "$2" "${3:-exit $1}"; fi; }
check_contains() {
  case "$2" in
    *"$1"*) ok "$3" ;;
    *) bad "$3" "wanted to see: $1" ;;
  esac
}
check_equal() { if [ "$1" = "$2" ]; then ok "$3"; else bad "$3" "wanted $2, got $1"; fi; }

printf 'smoke: leases and fencing tokens\n'

# the banner names the program, and the version comes from the generator
banner=$("$PY" -m "$MODULE" --version 2>&1); status=$?
check "$status" "version exits 0"
check_contains "$PROGRAM " "$banner" "the version banner names the program"

# help lists every command
help=$("$PY" -m "$MODULE" --help 2>&1); status=$?
check "$status" "help exits 0"
for command in demo model selftest; do
  check_contains "$command" "$help" "help lists $command"
done

# the demo runs and tells six stories
demo=$("$PY" -m "$MODULE" demo 2>&1); status=$?
check "$status" "demo exits 0"
for title in \
  "a lease alone cannot stop a paused holder" \
  "renewal is measured from now" \
  "a pause past the deadline ends the lease" \
  "the store's clock is the authority; the holder's is advisory" \
  "a release hands over with a fresh token" \
  "one token may write many times"; do
  check_contains "$title" "$demo" "demo story: $title"
done
check_contains "refused: token 1 is older than the last write (token 2)" "$demo" \
  "the fenced write is refused with both tokens"
check_contains "lost update" "$demo" "the unfenced write is named a lost update"
check_contains "fenced value after the ghost write" "$demo" "the demo prints the fenced value"

# model prints the timeline and the verdict
model=$("$PY" -m "$MODULE" model 2>&1); status=$?
check "$status" "model exits 0"
check_contains "acquire worker-a" "$model" "the timeline shows the first grant"
check_contains "acquire worker-b" "$model" "the timeline shows the second grant"
check_contains "until 2500" "$model" "the second token runs to 2500"
check_contains "write with token 1" "$model" "the timeline tries the stale write"
check_contains "refused: token 1 is older" "$model" "the stale write is refused"
check_contains "contract" "$model" "the timeline states the contract"
check_contains "kept" "$model" "the contract holds"

# a pause inside the lease demonstrates nothing, so it is refused
model=$("$PY" -m "$MODULE" model --ttl-ms 1000 --pause-ms 500 2>&1); status=$?
check_equal "$status" "2" "a pause inside the lease exits 2"
check_contains "never expires" "$model" "the refusal explains why"

# a zero ttl can never expire either
"$PY" -m "$MODULE" model --ttl-ms 0 >/dev/null 2>&1; status=$?
check_equal "$status" "2" "a zero ttl exits 2"

# a longer lease with a longer pause still works
model=$("$PY" -m "$MODULE" model --ttl-ms 2000 --pause-ms 2500 2>&1); status=$?
check "$status" "a 2500 ms pause inside a 2000 ms lease exits 0"
check_contains "until 4500" "$model" "the second token runs to 4500"

# selftest runs the same promises without pytest
selftest=$("$PY" -m "$MODULE" selftest 2>&1); status=$?
check "$status" "selftest exits 0"
check_contains "checks passed" "$selftest" "selftest reports its checks"

# an unknown command is a usage error, not a crash
"$PY" -m "$MODULE" nonsense >/dev/null 2>&1; status=$?
check_equal "$status" "2" "an unknown command exits 2"
"$PY" -m "$MODULE" >/dev/null 2>&1; status=$?
check_equal "$status" "2" "no command exits 2"

printf 'smoke: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
