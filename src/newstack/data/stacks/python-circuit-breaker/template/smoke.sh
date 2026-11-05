#!/usr/bin/env bash
# End-to-end smoke: the CLI a shell would actually call, its exit codes and its output.
set -uo pipefail

PY="${PY:-python}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
WORK="$(mktemp -d)"
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

c() { "$PY" -m "$MODULE" "$@"; }

# --- the demo -----------------------------------------------------------------
c demo >"$WORK/demo" 2>"$WORK/err"
check_equal "demo exits 0" 0 "$?"
check_match "the timeline is printed" '^t=   0.0' "$WORK/demo"
check_match "a healthy call is allowed" 'allow closed' "$WORK/demo"
check_match "the trip is on the timeline" 'deny  open' "$WORK/demo"
check_match "the probe is on the timeline" 'half-open, single probe' "$WORK/demo"
check_match "the demo recovers" 'verdict   recovered' "$WORK/demo"

c demo --failures 1 --cooldown 5 >"$WORK/one" 2>&1
check_equal "a one-failure scenario exits 0" 0 "$?"
check_match "and still recovers" 'verdict   recovered' "$WORK/one"

c demo --failures 3 --cooldown 12 --json >"$WORK/demo.json" 2>"$WORK/err"
check_equal "json demo exits 0" 0 "$?"
"$PY" -c 'import json,sys; print(json.load(open(sys.argv[1]))["ok"])' "$WORK/demo.json" \
  >"$WORK/ok" 2>&1
check_match "the json says it reproduced the timeline" '^True$' "$WORK/ok"
"$PY" -c 'import json,sys; d=json.load(open(sys.argv[1])); print(len(d["steps"]))' "$WORK/demo.json" \
  >"$WORK/steps" 2>&1
check_match "the json carries every step" '^9$' "$WORK/steps"
"$PY" -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d["steps"][-1]["state"])' \
  "$WORK/demo.json" >"$WORK/state" 2>&1
check_match "the last step is closed" '^closed$' "$WORK/state"

# --- refusals -----------------------------------------------------------------
c demo --failures 0 >"$WORK/out" 2>"$WORK/err"
check_equal "zero failures exits 2" 2 "$?"
check_match "and says why" 'failures must be at least 1' "$WORK/err"

c >"$WORK/out" 2>"$WORK/err"
check_equal "no subcommand exits 2" 2 "$?"

c demo --nonsense >"$WORK/out" 2>"$WORK/err"
check_equal "an unknown flag exits 2" 2 "$?"

# --- selftest and version -----------------------------------------------------
c selftest >"$WORK/selftest" 2>&1
check_equal "the selftest passes" 0 "$?"
check_match "and reports its count" 'checks passed, 0 failed' "$WORK/selftest"

c --version >"$WORK/version" 2>&1
check_equal "version exits 0" 0 "$?"
check_match "version prints a version" '^'"$PROGRAM"' [0-9]' "$WORK/version"

printf '\n%d passed, %d failed\n' "$PASSED" "$FAILED"
if [ "$FAILED" -ne 0 ]; then
  printf 'smoke: FAILED\n'
  exit 1
fi
printf 'smoke: all checks passed\n'
