#!/usr/bin/env bash
# Twelve checks of the numbers the README promises, run against the real CLI.
set -uo pipefail

PY="${PY:-.venv/bin/python}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
pass=0
fail=0

ok() { pass=$((pass + 1)); printf 'ok    %s\n' "$1"; }
bad() { fail=$((fail + 1)); printf 'FAIL  %s\n' "$1"; }
check_contains() {
  local description="$1" needle="$2" haystack="$3"
  case "$haystack" in
    *"$needle"*) ok "$description" ;;
    *) bad "$description (wanted '$needle')" ;;
  esac
}
check_equal() {
  local description="$1" want="$2" got="$3"
  if [ "$want" = "$got" ]; then ok "$description"; else bad "$description (wanted '$want', got '$got')"; fi
}
run() { "$PY" -m "$MODULE" "$@" 2>&1; }

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

output="$(run --version)"
check_contains "the version banner names the program" "$PROGRAM 0.1.0" "$output"

output="$(run report --events fixtures/traffic.jsonl --window 1h)"
check_equal "an hour with a five-minute outage exits 1" "1" "$?"
check_contains "and the report says so" "PAGE" "$output"
check_contains "the budget is spent" "already exhausted" "$output"

output="$(run report --events fixtures/traffic.jsonl --window 1h --json)"
check_contains "json mode still gates" '"firing": true' "$output"

output="$(run report --events fixtures/traffic.jsonl --window 30m --now "{{ year }}-01-01T00:00:00Z")"
check_equal "a --now that is before the data is refused" "2" "$?"

clean_now="$(python3 - "$tmp" <<'PYEOF'
import json, sys
from datetime import datetime, timezone
rows = [json.loads(line) for line in open("fixtures/traffic.jsonl", encoding="utf-8")]
moment = datetime.fromtimestamp(rows[30]["at"], tz=timezone.utc)
print(f"{moment:%Y-%m-%dT%H:%M:%SZ}")
PYEOF
)"
output="$(run report --events fixtures/traffic.jsonl --window 30m --now "$clean_now")"
check_equal "the same data, read before the outage, exits 0" "0" "$?"
check_contains "with no burn at all" "0.00x" "$output"

output="$(run report --events fixtures/traffic.jsonl --window 6h)"
check_contains "a window wider than the data names the hole" "silence is not success" "$output"

output="$(run report --events fixtures/traffic.jsonl --target 99,9)"
check_equal "a target that is not a percentage is unusable" "2" "$?"
check_contains "and says why" "not a percentage" "$output"

output="$(run report --events "$tmp/nope.jsonl")"
check_equal "a missing file is unusable" "2" "$?"

printf '{"at": 1772000010, "good": 1, "bad": 0}\n' > "$tmp/unaligned.jsonl"
output="$(run report --events "$tmp/unaligned.jsonl")"
check_equal "an unaligned bucket is unusable" "2" "$?"
check_contains "because every window it lands in is ambiguous" "not aligned" "$output"

output="$(run demo)"
check_equal "the demo exits 0" "0" "$?"
check_contains "and every report is as advertised" "0 not as advertised" "$output"

output="$(run selftest)"
check_equal "the selftest exits 0" "0" "$?"
check_contains "with nothing failing" "0 failed" "$output"

printf '\nsmoke: %d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ] | exit_status=$?
if [ "$fail" -eq 0 ]; then
  echo "smoke: all checks passed"
  exit 0
fi
echo "smoke: $fail check(s) failed"
exit 1
