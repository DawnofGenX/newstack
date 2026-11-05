#!/usr/bin/env bash
# Exercise the installed program the way a user would: real files, real exit codes.
set -uo pipefail

PY="${PY:-.venv/bin/python}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"

passed=0
failed=0
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

ok() {
  passed=$((passed + 1))
  printf 'ok   %s\n' "$1"
}

bad() {
  failed=$((failed + 1))
  printf 'FAIL %s\n' "$1"
  if [ -n "${2:-}" ]; then
    printf '     %s\n' "$2"
  fi
}

check_contains() {
  local name="$1" needle="$2" haystack="$3"
  if printf '%s' "$haystack" | grep -Fq -- "$needle"; then
    ok "$name"
  else
    bad "$name" "expected to find: $needle"
  fi
}

check_status() {
  local name="$1" wanted="$2" got="$3"
  if [ "$got" -eq "$wanted" ]; then
    ok "$name"
  else
    bad "$name" "exit $got, wanted $wanted"
  fi
}

# -- the banner names the program, not the package --------------------------
banner="$("$PY" -m "$MODULE" --version 2>&1)"
check_contains "the version banner names the program" "$PROGRAM " "$banner"

# -- a clean file ----------------------------------------------------------
out="$("$PY" -m "$MODULE" run --events fixtures/traffic.jsonl --width 60s 2>&1)"
status=$?
check_status "a clean file exits 0" 0 "$status"
check_contains "the header names the aggregation" "aggregation count" "$out"
check_contains "the watermark is printed" "watermark" "$out"
check_contains "the empty minute is reported as missing" "missing (1)" "$out"
check_contains "and it is minute three" "T00:03:00Z" "$out"
check_contains "windows are marked final" "final" "$out"

json="$work/report.json"
"$PY" -m "$MODULE" run --events fixtures/traffic.jsonl --json "$json" > /dev/null 2>&1
counts="$("$PY" - "$json" <<'PY'
import json, sys
payload = json.load(open(sys.argv[1]))
print(payload["aggregation"], len(payload["windows"]), len(payload["missing"]), payload["late"])
PY
)"
check_contains "the json report has seven windows and one gap" "count 7 1 []" "$counts"

# -- late data is a gate ---------------------------------------------------
out="$("$PY" -m "$MODULE" run --events fixtures/late.jsonl --width 60s 2>&1)"
status=$?
check_status "late data exits 1" 1 "$status"
check_contains "and the late row is named" "late arrival" "$out"
check_contains "with the window it belonged to" "T00:00:00Z..2026-01-01T00:01:00Z" "$out"

out="$("$PY" -m "$MODULE" run --events fixtures/late.jsonl --width 60s --lateness 10m 2>&1)"
status=$?
check_status "the same file is clean with a ten minute allowance" 0 "$status"

# -- how the aggregates treat nulls ---------------------------------------
cat > "$work/nulls.jsonl" <<'JSON'
{"t": "2026-01-01T00:00:05+00:00", "value": null}
{"t": "2026-01-01T00:00:06+00:00", "value": 4}
JSON
out="$("$PY" -m "$MODULE" run --events "$work/nulls.jsonl" --agg mean 2>&1)"
check_status "a mixed window exits 0" 0 "$?"
check_contains "the mean uses only the numbers" "4" "$out"

cat > "$work/allnull.jsonl" <<'JSON'
{"t": "2026-01-01T00:00:05+00:00", "value": null}
JSON
out="$("$PY" -m "$MODULE" run --events "$work/allnull.jsonl" --agg mean 2>&1)"
check_contains "the mean of nulls prints as a dash" "-" "$out"

# -- sliding windows -------------------------------------------------------
out="$("$PY" -m "$MODULE" run --events "$work/nulls.jsonl" --width 60s --hop 30s 2>&1)"
check_status "a sliding run exits 0" 0 "$?"
tiling="$("$PY" - "$json" <<'PY'
import json, sys
print(len(json.load(open(sys.argv[1]))["windows"]))
PY
)"
if [ "$tiling" -ge 2 ]; then
  ok "sliding windows overlap"
else
  bad "sliding windows overlap" "only $tiling window(s)"
fi

# -- refusals --------------------------------------------------------------
out="$("$PY" -m "$MODULE" run --events "$work/absent.jsonl" 2>&1)"
check_status "a missing file exits 2" 2 "$?"
check_contains "and says so" "absent.jsonl" "$out"

printf '{"t": "2026-01-01T00:00:00", "value": 1}\n' > "$work/naive.jsonl"
out="$("$PY" -m "$MODULE" run --events "$work/naive.jsonl" 2>&1)"
check_status "a naive timestamp exits 2" 2 "$?"
check_contains "and explains why" "local guess" "$out"

printf '{"t": "2026-01-01T00:00:00+00:00", "value": 1' > "$work/torn.jsonl"
out="$("$PY" -m "$MODULE" run --events "$work/torn.jsonl" 2>&1)"
check_status "a torn line exits 2" 2 "$?"

"$PY" -m "$MODULE" run --events fixtures/traffic.jsonl --agg median > /dev/null 2>&1
check_status "an unknown aggregation exits 2" 2 "$?"

"$PY" -m "$MODULE" run > /dev/null 2>&1
check_status "run without --events exits 2" 2 "$?"

# -- demo and selftest -----------------------------------------------------
out="$("$PY" -m "$MODULE" demo 2>&1)"
check_status "the demo exits 0" 0 "$?"
check_contains "the demo explains the watermark" "watermark" "$out"
check_contains "the demo shows a too-late row" "reason" "$out"

out="$("$PY" -m "$MODULE" selftest 2>&1)"
check_status "the selftest exits 0" 0 "$?"
check_contains "the selftest reports its count" "checks passed" "$out"

if [ "$failed" -eq 0 ]; then
  printf '\nsmoke: %d passed, 0 failed\n' "$passed"
  exit 0
fi
printf '\nsmoke: %d passed, %d failed\n' "$passed" "$failed"
exit 1
