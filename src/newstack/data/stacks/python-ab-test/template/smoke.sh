#!/usr/bin/env bash
# End-to-end checks for {{ npm_name }}: every claim the README makes, once.
set -uo pipefail

PY="${PY:-python3}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf 'ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf 'FAIL %s\n' "$1"; }

check() {  # check NAME COMMAND...
  local name="$1"
  shift
  if "$@" >"$WORK/out" 2>"$WORK/err"; then ok "$name"; else bad "$name: $(tail -n 3 "$WORK/err")"; fi
}

check_status() {  # check_status NAME EXPECTED COMMAND...
  local name="$1" expected="$2"
  shift 2
  "$@" >"$WORK/out" 2>"$WORK/err"
  local status=$?
  if [ "$status" -eq "$expected" ]; then
    ok "$name"
  else
    bad "$name: exit $status, wanted $expected ($(tail -n 2 "$WORK/err"))"
  fi
}

check_contains() {  # check_contains NAME NEEDLE COMMAND...
  local name="$1" needle="$2"
  shift 2
  "$@" >"$WORK/out" 2>"$WORK/err"
  if grep -qF -- "$needle" "$WORK/out"; then
    ok "$name"
  else
    bad "$name: '$needle' not in output"
  fi
}

check_equal() {  # check_equal NAME ACTUAL EXPECTED
  if [ "$2" = "$3" ]; then ok "$1"; else bad "$1: '$2' is not '$3'"; fi
}

run() { "$PY" -m "$MODULE" "$@"; }

json() { "$PY" -c 'import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])' "$1" "$2"; }

check_contains "the version banner names the program" "$PROGRAM " run --version
check_contains "help explains the tool" "A/B test maths" run --help

# The arms in the fixture are the arms in the story.
check_equal "the fixture control rate is 100/1000" \
  "$("$PY" -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d["control"]["conversions"], d["control"]["visitors"])' \
    fixtures/arms.json)" "100 1000"

check_status "a real difference compares cleanly" 0 \
  run compare --control control=100/1000 --treatment treatment=130/1000
check_contains "compare prints the difference" "+0.0300" \
  run compare --control control=100/1000 --treatment treatment=130/1000
check_contains "compare prints the p-value" "0.0355" \
  run compare --control control=100/1000 --treatment treatment=130/1000
check_contains "compare names the direction" "higher" \
  run compare --control control=100/1000 --treatment treatment=130/1000
check_contains "compare prints a wilson interval per arm" "wilson" \
  run compare --control control=100/1000 --treatment treatment=130/1000
check_contains "compare warns about the horizon" "fixed-horizon" \
  run compare --control control=100/1000 --treatment treatment=130/1000

run compare --control control=100/1000 --treatment treatment=130/1000 --json >"$WORK/compare.json" 2>"$WORK/err"
check "compare --json writes a file" test -s "$WORK/compare.json"
check_equal "the json z is the printed z" \
  "$("$PY" -c 'import json,sys; print("%.4f" % json.load(open(sys.argv[1]))["z"])' "$WORK/compare.json")" \
  "2.1027"
check_equal "the json names the direction" "$(json "$WORK/compare.json" direction)" "higher"
check_equal "the json is significant" "$(json "$WORK/compare.json" significant)" "True"

check_status "a traffic imbalance is refused" 1 \
  run srm --control control=500/102000 --treatment treatment=500/100000
check_contains "srm names the mismatch" "MISMATCH" \
  run srm --control control=500/102000 --treatment treatment=500/100000
check_status "a plausible split passes" 0 \
  run srm --control control=500/50100 --treatment treatment=500/50000
check_contains "srm names the split" "split" \
  run srm --control control=500/50100 --treatment treatment=500/50000

check_contains "power prints the sample size" "57,763" \
  run power --baseline 0.10 --lift 0.05
check_contains "power prints both arms" "115,526" \
  run power --baseline 0.10 --lift 0.05
check_contains "power says what a smaller sample could catch" "8.56%" \
  run power --baseline 0.10 --lift 0.05 --visitors 20000

check_status "peeking gates on its own spending" 0 \
  run peeking --trials 300 --visitors 2000 --looks 5 --seed 5
check_contains "peeking prints the flat line" "every look" \
  run peeking --trials 300 --visitors 2000 --looks 5 --seed 5
check_contains "peeking prints the boundary" "boundary held" \
  run peeking --trials 300 --visitors 2000 --looks 5 --seed 5

run peeking --trials 200 --visitors 1000 --looks 4 --seed 3 --json >"$WORK/peek.json" 2>"$WORK/err"
check "peeking --json writes a file" test -s "$WORK/peek.json"
check_equal "the json carries four critical values" \
  "$("$PY" -c 'import json,sys; print(len(json.load(open(sys.argv[1]))["critical"]))' "$WORK/peek.json")" "4"

check_status "a malformed arm is a usage error" 2 \
  run compare --control control=10 --treatment treatment=1/10
check_status "an impossible baseline is a usage error" 2 \
  run power --baseline 1.5 --lift 0.05
check_status "a missing command is an error" 2 run
check_status "a boundary needs at least one look" 2 \
  run peeking --trials 10 --visitors 100 --looks 0

run demo >"$WORK/demo.out" 2>"$WORK/err"
check "the demo runs" test -s "$WORK/demo.out"
check_equal "the demo has six stories" "$(grep -c -- '  -> ' "$WORK/demo.out")" "6"
if grep -qF -- "-> BROKEN" "$WORK/demo.out"; then
  bad "every demo story must hold"
else
  ok "every demo story holds"
fi
check_contains "the demo names the sample size decision" "57,763" cat "$WORK/demo.out"

check_contains "the selftest passes" "checks passed" run selftest

printf '\n%d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ] && printf 'smoke: all checks passed\n'
[ "$FAILED" -eq 0 ]
