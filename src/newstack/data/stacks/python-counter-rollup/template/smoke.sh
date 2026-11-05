#!/usr/bin/env bash
# Proves the claims in README.md against the built package, on real readings.
set -uo pipefail

PY="${PY:-python}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

passed=0
failed=0
ok() { passed=$((passed + 1)); printf 'ok    %s\n' "$1"; }
bad() { failed=$((failed + 1)); printf 'FAIL  %s\n' "$1"; }
contains() {
  local name="$1" haystack="$2" needle="$3"
  case "$haystack" in
    *"$needle"*) ok "$name" ;;
    *) bad "$name (wanted '$needle' in the output)" ;;
  esac
}
run() { "$@" >"$WORK/out" 2>"$WORK/err"; status=$?; }

# A steady counter: 100 events every 10 s.
printf '%s\n' '{"at_us": 0, "value": 0}' '{"at_us": 10000000, "value": 100}' \
  '{"at_us": 20000000, "value": 200}' '{"at_us": 30000000, "value": 300}' >"$WORK/steady.jsonl"
# One scrape missing between 20 s and 40 s.
printf '%s\n' '{"at_us": 0, "value": 0}' '{"at_us": 10000000, "value": 10}' \
  '{"at_us": 20000000, "value": 20}' '{"at_us": 40000000, "value": 40}' \
  '{"at_us": 50000000, "value": 50}' >"$WORK/holed.jsonl"
# The counter restarts between two scrapes.
printf '%s\n' '{"at_us": 0, "value": 500}' '{"at_us": 10000000, "value": 600}' \
  '{"at_us": 20000000, "value": 20}' >"$WORK/reset.jsonl"

run "$PY" -m "$MODULE" --version
contains "the version banner names the program" "$(cat "$WORK/out")" "$PROGRAM 0.1.0"

run "$PY" -m "$MODULE" rollup --file "$WORK/steady.jsonl" --width 10 --name requests
out="$(cat "$WORK/out")"
[ "$status" -eq 0 ] && ok "a clean rollup exits 0" || bad "a clean rollup exits 0 (got $status)"
contains "the table has a header" "$out" "name         shard"
contains "a steady counter reports 10.000/s" "$out" "rate     10.000/s"
contains "three windows have readings" "$out" "windows  3 with readings, 0 without"
contains "the rate is described as measured" "$out" "over the windows that were actually measured"

run "$PY" -m "$MODULE" rollup --file "$WORK/steady.jsonl" --width 10 --json
out="$(cat "$WORK/out")"
contains "json carries the window width" "$out" '"width_us": 10000000'
contains "json has no gaps" "$out" '"gaps": []'
contains "json carries the rate" "$out" '"rate_per_second": 10.0'

run "$PY" -m "$MODULE" rollup --file "$WORK/holed.jsonl" --width 10
out="$(cat "$WORK/out")"
[ "$status" -eq 1 ] && ok "a missing window exits 1" || bad "a missing window exits 1 (got $status)"
contains "the gap is located" "$out" "gap      window 30000000..40000000 has no reading"
contains "the gap is not called zero" "$out" "that window is unknown, not zero"
contains "the rate divides by observed time" "$out" "rate     1.000/s"

run "$PY" -m "$MODULE" rollup --file "$WORK/reset.jsonl" --width 10 --json
out="$(cat "$WORK/out")"
contains "a restart is counted" "$out" '"resets": 1'
contains "a restart is the new value" "$out" '"total": 20'
if grep -q '"total": -' "$WORK/out"; then bad "no window is negative"; else ok "no window is negative"; fi

run "$PY" -m "$MODULE" rollup --file "$WORK/reset.jsonl" --width 10 --shard a --json
cp "$WORK/out" "$WORK/a.json"
cp "$WORK/a.json" "$WORK/b.json"

run "$PY" -m "$MODULE" merge "$WORK/a.json" "$WORK/b.json"
out="$(cat "$WORK/out")"
[ "$status" -eq 0 ] && ok "merging repeats exits 0" || bad "merging repeats exits 0 (got $status)"
contains "a repeated delivery is dropped" "$out" "2 repeat(s) dropped"
contains "the shards are added together" "$out" "combined across shards"

"$PY" - "$WORK/a.json" "$WORK/conflict.json" <<'PYEOF'
import json, sys
payload = json.load(open(sys.argv[1]))
payload["rollups"][0]["total"] += 1
json.dump(payload, open(sys.argv[2], "w"))
PYEOF
run "$PY" -m "$MODULE" merge "$WORK/a.json" "$WORK/conflict.json"
[ "$status" -eq 2 ] && ok "a disagreeing repeat exits 2" || bad "a disagreeing repeat exits 2 (got $status)"
contains "the refusal names the shard" "$(cat "$WORK/err")" "one of them is wrong"

run "$PY" -m "$MODULE" rollup --file "$WORK/nope.jsonl"
[ "$status" -eq 2 ] && ok "a missing file exits 2" || bad "a missing file exits 2 (got $status)"
contains "a missing file is named" "$(cat "$WORK/err")" "cannot read"

: >"$WORK/empty.jsonl"
run "$PY" -m "$MODULE" rollup --file "$WORK/empty.jsonl"
[ "$status" -eq 2 ] && ok "an empty file exits 2" || bad "an empty file exits 2 (got $status)"
contains "an empty file says why" "$(cat "$WORK/err")" "holds no readings"

run "$PY" -m "$MODULE" demo
contains "demo proves all four scenarios" "$(cat "$WORK/out")" "0 not as advertised"
[ "$status" -eq 0 ] && ok "demo exits 0" || bad "demo exits 0 (got $status)"

run "$PY" -m "$MODULE" selftest
contains "the selftest reports no failures" "$(cat "$WORK/out")" "0 failed"
[ "$status" -eq 0 ] && ok "selftest exits 0" || bad "selftest exits 0 (got $status)"

run "$PY" -m "$MODULE" --help
contains "the help names the merge command" "$(cat "$WORK/out")" "merge"

printf '\n%d passed, %d failed\n' "$passed" "$failed"
if [ "$failed" -ne 0 ]; then
  echo "smoke: FAILED"
  exit 1
fi
echo "smoke: all checks passed"
