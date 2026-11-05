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

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

printf 'smoke: count-min sketch\n'

banner=$("$PY" -m "$MODULE" --version 2>&1); status=$?
check "$status" "version exits 0"
check_contains "$PROGRAM " "$banner" "the version banner names the program"

help=$("$PY" -m "$MODULE" --help 2>&1); status=$?
check "$status" "help exits 0"
for command in add estimate info merge demo selftest; do
  check_contains "$command" "$help" "help lists $command"
done

# add creates a sketch and reports its shape
created=$("$PY" -m "$MODULE" add --sketch "$work/seen.json" --items apple pear apple --width 64 --depth 4 2>&1); status=$?
check "$status" "add exits 0"
check_contains "3" "$created" "add reports the three updates"

# an item added twice estimates 2, and a stranger estimates 0
json=$("$PY" -m "$MODULE" estimate --sketch "$work/seen.json" --item apple --json 2>&1)
check_contains '"estimate": 2' "$json" "apple estimates 2"
json=$("$PY" -m "$MODULE" estimate --sketch "$work/seen.json" --item durian --json 2>&1)
check_contains '"estimate": 0' "$json" "an unseen item estimates 0"

# info prints the shape and the promise
info=$("$PY" -m "$MODULE" info --sketch "$work/seen.json" 2>&1); status=$?
check "$status" "info exits 0"
check_contains "width        64" "$info" "info prints the width"
check_contains "promise" "$info" "info prints the error promise"

# the human-readable estimate explains its own error
plain=$("$PY" -m "$MODULE" estimate --sketch "$work/seen.json" --item apple 2>&1)
check_contains "can be at most" "$plain" "an estimate states its bound"

# merge adds the counters pointwise
"$PY" -m "$MODULE" add --sketch "$work/a.json" --items apple --count 3 --width 64 --depth 4 >/dev/null
"$PY" -m "$MODULE" add --sketch "$work/b.json" --items apple --count 2 --width 64 --depth 4 >/dev/null
merged=$("$PY" -m "$MODULE" merge --left "$work/a.json" --right "$work/b.json" --out "$work/m.json" 2>&1); status=$?
check "$status" "merge exits 0"
check_contains "pointwise" "$merged" "merge explains that it is exact"
json=$("$PY" -m "$MODULE" estimate --sketch "$work/m.json" --item apple --json 2>&1)
check_contains '"estimate": 5' "$json" "the merged estimate is 5"

# the gates: unusable input exits 2 and says why
"$PY" -m "$MODULE" estimate --sketch "$work/missing.json" --item apple >/dev/null 2>&1; status=$?
check_equal "$status" "2" "a missing sketch exits 2"
"$PY" -m "$MODULE" add --sketch "$work/seen.json" --items apple --count 0 >/dev/null 2>&1; status=$?
check_equal "$status" "2" "a zero count exits 2"
"$PY" -m "$MODULE" add --sketch "$work/wide.json" --items apple --width 128 --depth 4 >/dev/null
"$PY" -m "$MODULE" merge --left "$work/a.json" --right "$work/wide.json" --out "$work/x.json" >/dev/null 2>&1; status=$?
check_equal "$status" "2" "merging different shapes exits 2"
"$PY" -m "$MODULE" >/dev/null 2>&1; status=$?
check_equal "$status" "2" "no command exits 2"

# the demo runs and keeps its promises
demo=$("$PY" -m "$MODULE" demo 2>&1); status=$?
check "$status" "demo exits 0"
for title in \
  "an estimate is never below the truth" \
  "the error is bounded by e/width" \
  "more width means less error" \
  "two halves merged equal one pass" \
  "conservative update lowers the mean overestimate" \
  "the heaviest items survive"; do
  check_contains "$title" "$demo" "demo story: $title"
done
check_contains "underestimates     0" "$demo" "the demo counts zero underestimates"
check_contains "rows identical     True" "$demo" "the demo proves the merge is exact"

selftest=$("$PY" -m "$MODULE" selftest 2>&1); status=$?
check "$status" "selftest exits 0"
check_contains "checks passed" "$selftest" "selftest reports its checks"

printf 'smoke: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
