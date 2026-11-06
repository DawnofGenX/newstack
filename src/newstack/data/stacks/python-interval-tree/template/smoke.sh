#!/usr/bin/env bash
# The smoke test runs the tool the way a user would and checks what it says.
# PY points at the interpreter that has this package installed.
set -uo pipefail

PY="${PY:-python3}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

check_contains() {
  local name="$1" needle="$2" text="$3"
  if [[ "$text" == *"$needle"* ]]; then
    ok "$name"
  else
    bad "$name"
    printf '       wanted %q in %q\n' "$needle" "${text:0:200}"
  fi
}

check_equal() {
  local name="$1" want="$2" got="$3"
  if [[ "$want" == "$got" ]]; then
    ok "$name"
  else
    bad "$name"
    printf '       wanted %q, got %q\n' "$want" "$got"
  fi
}

run() {
  OUT=$("$@" 2>&1)
  STATUS=$?
}

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

echo "smoke: $PROGRAM"

run "$PY" -m "$MODULE" --version
check_equal "the version names the program" 0 "$STATUS"
check_contains "the banner carries the version" "0.1.0" "$OUT"

run "$PY" -m "$MODULE" --help
check_equal "help exits zero" 0 "$STATUS"
check_contains "help lists the subcommands" "selftest" "$OUT"

# --- building the tree ------------------------------------------------------------
SPANS="$WORK/spans.txt"
printf '# a comment\n1 5\n3 9\n6 12\n' >"$SPANS"

run "$PY" -m "$MODULE" load --intervals "$SPANS"
check_equal "load exits zero" 0 "$STATUS"
check_contains "the tree names its size" "spans      3 held" "$OUT"

run "$PY" -m "$MODULE" load --intervals "$SPANS" --json
SHAPE=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["corpus"])' "$OUT")
check_equal "the walk is the sorted corpus" "['[1..5)', '[3..9)', '[6..12)']" "$SHAPE"

run "$PY" -m "$MODULE" load --intervals "$WORK/missing.txt"
check_equal "a missing span list is unusable" 2 "$STATUS"
check_contains "the file is named" "no such span list" "$OUT"

# --- stabbing ----------------------------------------------------------------------
run "$PY" -m "$MODULE" stab --intervals "$SPANS" --point 4
check_equal "a held point exits zero" 0 "$STATUS"
check_contains "the inside is named" "held       2 span(s)" "$OUT"

run "$PY" -m "$MODULE" stab --intervals "$SPANS" --point 12
check_equal "an end stands outside" 1 "$STATUS"

run "$PY" -m "$MODULE" stab --intervals "$SPANS" --point 5
check_equal "one end out, the neighbour answers" 0 "$STATUS"
check_contains "the neighbour alone is held" "held       1 span(s)" "$OUT"

run "$PY" -m "$MODULE" stab --intervals "$SPANS" --point 100
check_equal "a far point exits one" 1 "$STATUS"

run "$PY" -m "$MODULE" stab --intervals "$SPANS" --point 4 --json
STABBED=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["count"])' "$OUT")
check_equal "stab --json is only json" "2" "$STABBED"

# --- the window ----------------------------------------------------------------------
run "$PY" -m "$MODULE" overlap --intervals "$SPANS" --low 2 --high 8
check_equal "a touching window exits zero" 0 "$STATUS"
check_contains "the window is stated" "window     [2..8)" "$OUT"

run "$PY" -m "$MODULE" overlap --intervals "$SPANS" --low 9 --high 10
check_equal "a touching end misses" 0 "$STATUS"

run "$PY" -m "$MODULE" overlap --intervals "$SPANS" --low 50 --high 60
check_equal "a distant window exits one" 1 "$STATUS"

run "$PY" -m "$MODULE" overlap --intervals "$SPANS" --low 9 --high 3
check_equal "an inverted window is unusable" 2 "$STATUS"

# --- first match ----------------------------------------------------------------------
run "$PY" -m "$MODULE" first --intervals "$SPANS" --point 7
check_equal "first finds the earliest" 0 "$STATUS"
check_contains "the earliest is named" "first      [3..9)" "$OUT"

run "$PY" -m "$MODULE" first --intervals "$SPANS" --point 100
check_equal "first without a match exits one" 1 "$STATUS"

# --- the fixture corpus ------------------------------------------------------------------
HITS=0
while IFS= read -r line; do
  [[ -z "$line" || "$line" == \#* ]] && continue
  point=$(printf '%s' "$line" | awk '{print int(($1 + $2) / 2)}')
  HITS=$((HITS + 1))
  run "$PY" -m "$MODULE" stab --intervals fixtures/spans.txt --point "$point"
  if [[ "$STATUS" -eq 0 ]]; then ok "fixture span holds its midpoint $point"; else bad "fixture span lost $point"; fi
done <fixtures/spans.txt
if [[ "$HITS" -ge 20 ]]; then ok "the fixture holds a corpus ($HITS spans)"; else bad "the fixture is too small ($HITS spans)"; fi

# --- the invariants -----------------------------------------------------------------------
run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
