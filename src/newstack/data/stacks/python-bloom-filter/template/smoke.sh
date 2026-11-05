#!/usr/bin/env bash
# smoke.sh — drive the CLI end to end, the way a person would.
set -uo pipefail

PY="${PY:-python3}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
WORK="$(mktemp -d)"
FILTER="$WORK/items.json"
trap 'rm -rf "$WORK"' EXIT

passed=0
failed=0
ok() { printf 'ok    %s\n' "$1"; passed=$((passed + 1)); }
bad() { printf 'FAIL  %s\n' "$1"; failed=$((failed + 1)); }
check_equal() {
  if [ "$2" = "$3" ]; then ok "$1"; else bad "$1 (got '$2', want '$3')"; fi
}
check_contains() {
  case "$2" in *"$3"*) ok "$1" ;; *) bad "$1 (no '$3' in: $2)" ;; esac
}

run() { out=$("$@" 2>&1); status=$?; }

run "$PY" -m "$MODULE" --version
check_contains "the version banner names the program" "$out" "$PROGRAM"
check_contains "the version banner names a version" "$out" "0.1.0"

run "$PY" -m "$MODULE" sized --expected 1000 --rate 0.01
check_equal "sized exits zero" "$status" "0"
check_contains "sized computes 9586 bits" "$out" "bits        9586"
check_contains "sized computes 7 hashes" "$out" "hashes      7"

run "$PY" -m "$MODULE" sized --expected 1000 --json
check_contains "sized answers in json" "$out" '"m_bits": 9586'

run "$PY" -m "$MODULE" create --filter "$FILTER" --expected 1000
check_equal "create exits zero" "$status" "0"
check_contains "create reports the bits" "$out" "bits        9586"
test -s "$FILTER" && ok "create wrote a filter file" || bad "create wrote a filter file"

run "$PY" -m "$MODULE" create --filter "$FILTER" --expected 10
check_equal "a second create is refused" "$status" "2"
check_contains "the refusal names --force" "$out" "--force"

run "$PY" -m "$MODULE" create --filter "$FILTER" --expected 10 --force
check_equal "create --force replaces the filter" "$status" "0"

run "$PY" -m "$MODULE" add --filter "$FILTER" --item alpha --item beta
check_equal "add exits zero" "$status" "0"
check_contains "add reports fresh bits" "$out" "new bits 7 of 7"

run "$PY" -m "$MODULE" add --filter "$FILTER" --item alpha
check_contains "re-adding an item sets nothing" "$out" "new bits 0 of 7"

run "$PY" -m "$MODULE" check --filter "$FILTER" --item alpha
check_equal "an added item exits zero" "$status" "0"
check_contains "a yes is a maybe" "$out" "maybe: false positives are possible"

run "$PY" -m "$MODULE" check --filter "$FILTER" --item gamma
check_equal "an unadded item exits one" "$status" "1"
check_contains "a no is definite" "$out" "definite"

run "$PY" -m "$MODULE" check --filter "$FILTER" --item gamma --json
check_contains "the json answer is false" "$out" '"present": false'

run "$PY" -m "$MODULE" info --filter "$FILTER"
check_equal "info exits zero while healthy" "$status" "0"
check_contains "info reports the verdict" "$out" "verdict           healthy"
check_contains "info reports the estimate" "$out" "estimated items"

run "$PY" -m "$MODULE" info --filter "$FILTER" --json
check_contains "info answers in json" "$out" '"saturated": false'

COUNTING="$WORK/counting.json"
run "$PY" -m "$MODULE" create --filter "$COUNTING" --expected 100 --kind counting
check_equal "a counting filter can be created" "$status" "0"
check_contains "create names the kind" "$out" "counting-bloom"
run "$PY" -m "$MODULE" add --filter "$COUNTING" --item alpha
run "$PY" -m "$MODULE" check --filter "$COUNTING" --item alpha
check_equal "the counting filter answers yes" "$status" "0"
run "$PY" -m "$MODULE" info --filter "$COUNTING"
check_contains "counters are reported" "$out" "saturated counters"

SMALL="$WORK/small.json"
run "$PY" -m "$MODULE" create --filter "$SMALL" --expected 1
for number in $(seq 1 40); do
  "$PY" -m "$MODULE" add --filter "$SMALL" --item "item-$number" >/dev/null 2>&1
done
run "$PY" -m "$MODULE" info --filter "$SMALL"
check_equal "a saturated filter exits one from info" "$status" "1"
check_contains "the verdict says saturated" "$out" "saturated"

run "$PY" -m "$MODULE" check --filter "$WORK/nope.json" --item alpha
check_equal "a missing filter is a usage error" "$status" "2"
check_contains "the error names the fix" "$out" "create one with"

run "$PY" -m "$MODULE" create --filter "$WORK/bad.json" --expected 10 --rate 0
check_equal "a rate of zero is a usage error" "$status" "2"
check_contains "the error explains the range" "$out" "between 0 and 1"

run "$PY" -m "$MODULE" demo
check_equal "demo exits zero" "$status" "0"
check_contains "the demo proves the one guarantee" "$out" "no false negatives"
check_contains "the demo measures the rate" "$out" "the false-positive rate is a number you can check"
check_contains "the demo breaks removal" "$out" "removal is where the guarantee dies"
check_contains "the demo shows saturation" "$out" "saturation is the failure mode"

run "$PY" -m "$MODULE" selftest
check_equal "selftest exits zero" "$status" "0"
check_contains "selftest counts its checks" "$out" "checks passed"

run "$PY" -m "$MODULE" --help
check_contains "help lists create" "$out" "create"

printf '\nsmoke: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
