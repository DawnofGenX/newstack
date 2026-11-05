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

printf 'smoke: hyperloglog\n'

banner=$("$PY" -m "$MODULE" --version 2>&1); status=$?
check "$status" "version exits 0"
check_contains "$PROGRAM " "$banner" "the version banner names the program"

help=$("$PY" -m "$MODULE" --help 2>&1); status=$?
check "$status" "help exits 0"
for command in build estimate merge info demo selftest; do
  check_contains "$command" "$help" "help lists $command"
done

# build reads stdin and reports the shape of what it stored
built=$(printf 'a\nb\nc\n' | "$PY" -m "$MODULE" build --sketch "$work/small.json" --precision 10 2>&1)
status=$?
check "$status" "build exits 0"
check_contains "items     3" "$built" "build counts the items it read"
check_contains "estimate  3" "$built" "three distinct items estimate as three"

info=$("$PY" -m "$MODULE" estimate --sketch "$work/small.json" 2>&1); status=$?
check "$status" "estimate exits 0"
check_contains "promised  3.25%" "$info" "the estimate prints the promised error"

gated=$("$PY" -m "$MODULE" estimate --sketch "$work/small.json" --expect 3 2>&1); status=$?
check "$status" "an accurate estimate passes its gate"
check_contains "error     +0.00%" "$gated" "the gate prints the measured error"

"$PY" -m "$MODULE" estimate --sketch "$work/small.json" --expect 3000 >/dev/null 2>&1; status=$?
check_equal "$status" "1" "a wrong expectation exits 1"

# a larger stream, built twice at the same precision, merges losslessly
python3 -c 'print("\n".join(f"item:{index}" for index in range(2000)))' > "$work/items.txt"
"$PY" -m "$MODULE" build --input "$work/items.txt" --sketch "$work/a.json" --precision 12 >/dev/null 2>&1
status=$?
check "$status" "a file of items builds"
merged=$("$PY" -m "$MODULE" merge --left "$work/a.json" --right "$work/a.json" --out "$work/m.json" 2>&1)
status=$?
check "$status" "merging equal precisions exits 0"
check_contains "union" "$merged" "the merge reports the union"

"$PY" -m "$MODULE" build --input "$work/items.txt" --sketch "$work/b.json" --precision 14 >/dev/null 2>&1
"$PY" -m "$MODULE" merge --left "$work/a.json" --right "$work/b.json" --out "$work/x.json" >/dev/null 2>"$work/err.txt"
status=$?
check_equal "$status" "2" "merging different precisions exits 2"
check_contains "reinterpreted" "$(cat "$work/err.txt")" "the refusal says why"

"$PY" -m "$MODULE" estimate --sketch "$work/absent.json" >/dev/null 2>&1; status=$?
check_equal "$status" "2" "a missing sketch exits 2"

printf '{nope' > "$work/broken.json"
"$PY" -m "$MODULE" estimate --sketch "$work/broken.json" >/dev/null 2>&1; status=$?
check_equal "$status" "2" "a corrupt sketch exits 2"

demo=$("$PY" -m "$MODULE" demo 2>&1); status=$?
check "$status" "the demo exits 0"
check_contains "1. an estimate beside the memory" "$demo" "the demo prints story one"
check_contains "5. a hash without entropy" "$demo" "the demo prints story five"
check_equal "$(grep -c -- '-> holds' <<<"$demo")" "6" "every story holds"
if grep -q 'BROKEN' <<<"$demo"; then bad "no story claims to be broken"; else ok "no story claims to be broken"; fi

selftest=$("$PY" -m "$MODULE" selftest 2>&1); status=$?
check "$status" "selftest exits 0"
check_contains "checks passed" "$selftest" "selftest reports its checks"

json=$("$PY" -m "$MODULE" info --sketch "$work/a.json" --json 2>&1); status=$?
check "$status" "info --json exits 0"
check_contains '"registers": 4096' "$json" "info reports the register count"

printf '\nsmoke: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ] || exit 1
printf 'smoke: all checks passed\n'
