#!/usr/bin/env bash
# Fifteen checks of the decisions the README promises, run against the real CLI.
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

output="$(run --version)"
check_contains "the version banner names the program" "$PROGRAM " "$output"

output="$(run --help)"
check_contains "help shows the commands" "decide" "$output"

output="$(run decide --policy fixtures/policy.json --subject alice \
  --action docs:write --resource project:acme/doc:42)"
status=$?
check_equal "an inherited write inside the scope exits 0" "0" "$status"
check_contains "and names the winning rule" "ALLOW  by allow-write" "$output"
check_contains "the trace shows the scope" "editor@project:acme" "$output"

output="$(run decide --policy fixtures/policy.json --subject alice \
  --action docs:write --resource project:other/doc:42)"
status=$?
check_equal "the same write outside the scope is denied" "1" "$status"
check_contains "and explains the scope" "holds none of the roles editor" "$output"

output="$(run decide --policy fixtures/policy.json --subject carol \
  --action docs:read --resource project:acme/secret)"
status=$?
check_equal "a deny outranks a matching allow" "1" "$status"
check_contains "the deny is the winner" "DENY   by deny-secret" "$output"
check_contains "the allow is still shown as a match" "MATCH  allow  allow-read" "$output"

output="$(run decide --policy fixtures/policy.json --subject mallory \
  --action docs:read --resource project:acme/doc:1)"
check_equal "an unassigned subject is denied" "1" "$?"
check_contains "the default is stated rather than implied" "by default: no rule matched" "$output"

output="$(run decide --policy fixtures/policy.json --subject carol \
  --action comments:create --resource project:acme/doc:7 \
  --subject-attr id=carol --resource-attr owner=carol)"
check_equal "a satisfied condition grants" "0" "$?"
check_contains "the condition is reported met" "MATCH  allow  allow-comment" "$output"

output="$(run decide --policy fixtures/policy.json --subject carol \
  --action comments:create --resource project:acme/doc:7 --subject-attr id=carol)"
check_equal "a missing attribute does not grant" "1" "$?"
check_contains "and the trace says it is missing" "missing" "$output"

output="$(run decide --policy fixtures/policy.json --subject alice \
  --action docs:read --resource project:acme/doc:1 --json)"
check_contains "json mode carries the decision" '"allowed": true' "$output"

output="$(run check --policy fixtures/policy.json)"
check_equal "the shipped policy passes its own check" "0" "$?"
check_contains "and says so" "no findings" "$output"

output="$(run check --policy fixtures/dead-role.json)"
check_equal "a role nobody holds is a finding" "1" "$?"
check_contains "the finding names the role" "audit-ghost" "$output"

output="$(run decide --policy fixtures/cycle.json --subject alice \
  --action docs:read --resource project:acme/doc:1)"
check_equal "an inheritance cycle is refused" "2" "$?"
check_contains "the cycle is named" "inherits itself" "$output"

output="$(run decide --policy fixtures/policy.json --subject alice \
  --action docs:read --resource project:acme/doc:1 --subject-attr noequals)"
check_equal "a malformed attribute is a usage error" "2" "$?"
check_contains "the flag is named" "KEY=VALUE" "$output"

output="$(run demo)"
check_equal "the demo runs" "0" "$?"
check_contains "and shows the one-segment trap" "project:acme/doc:42  False" "$output"

output="$(run selftest)"
check_equal "the selftest passes" "0" "$?"
check_contains "and says so" "all checks passed" "$output"

printf '\nsmoke: %d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
