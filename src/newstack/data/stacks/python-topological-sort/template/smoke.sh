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
check_equal "the version exits zero" 0 "$STATUS"
check_contains "the banner carries the version" "0.1.0" "$OUT"

run "$PY" -m "$MODULE" --help
check_equal "help exits zero" 0 "$STATUS"
check_contains "help lists the subcommands" "selftest" "$OUT"

# --- the listing, the check, and the fixed point ---------------------------------------------
run "$PY" -m "$MODULE" order 1 2 3 4 "1>2" "1>4" "2>3" "4>3"
check_equal "a listing exits zero" 0 "$STATUS"
check_equal "the ladder lists least first" "1>2>4>3" "$OUT"

run "$PY" -m "$MODULE" order --json 1 2 3 "1>2" "2>3"
check_equal "a json listing exits zero" 0 "$STATUS"
check_contains "the json answers the sequence" '"order": [1, 2, 3]' "$OUT"

run "$PY" -m "$MODULE" check "1>2>4>3" 1 2 3 4 "1>2" "1>4" "2>3" "4>3"
check_equal "a held listing exits zero" 0 "$STATUS"
check_contains "the check names the hold" "holds" "$OUT"

run "$PY" -m "$MODULE" check "2>1>3" 1 2 3 "1>2" "2>3"
check_equal "a broken listing exits one" 1 "$STATUS"
check_contains "the check names the break" "broken" "$OUT"

run "$PY" -m "$MODULE" cycles 1 2 3 "1>2" "2>3"
check_equal "a clear graph exits zero" 0 "$STATUS"
check_contains "the clear graph is named clear" "clear" "$OUT"

run "$PY" -m "$MODULE" cycles 1 2 3 "1>2" "2>3" "3>1"
check_equal "a tangle exits zero" 0 "$STATUS"
check_contains "the tangle names its cycle" "cycle 1>2>3" "$OUT"

run "$PY" -m "$MODULE" order 1 2 3 "1>2" "2>3" "3>1"
check_equal "a tangle refuses the listing" 2 "$STATUS"
check_contains "the refusal names the block" "tangled" "$OUT"

# --- the edges the door refuses --------------------------------------------------------------
run "$PY" -m "$MODULE" order a b
check_equal "a word is not a graph" 2 "$STATUS"
check_contains "the token is named" "no integer label" "$OUT"

run "$PY" -m "$MODULE" order 1.5
check_equal "a float is not a label" 2 "$STATUS"

run "$PY" -m "$MODULE" order "1>2>3"
check_equal "a half pair is refused" 2 "$STATUS"

run "$PY" -m "$MODULE" report --corpus "$WORK/missing.txt"
check_equal "a missing corpus exits two" 2 "$STATUS"

# --- the fixture corpus, listing after listing ------------------------------------------------
COUNT=$(grep -cvE '^[[:space:]]*(#|$)' fixtures/graphs.txt)
if [[ "$COUNT" -ge 8 ]]; then
  ok "the fixture holds a corpus ($COUNT graphs)"
else
  bad "the fixture is too small ($COUNT graphs)"
fi

BROKE=$("$PY" - <<'PYEOF'
from {{ package_name }}.corpus import load_graphs
from {{ package_name }}.cycle import cycle
from {{ package_name }}.oracle import naive_order
from {{ package_name }}.order import order, validate

broken = []
for graph in load_graphs("fixtures/graphs.txt"):
    listed = order(graph)
    if cycle(graph) is not None or validate(graph, listed):
        broken.append(graph.to_text())
        continue
    if listed != naive_order(graph) or order(graph) != listed:
        broken.append(graph.to_text())
print(len(broken))
PYEOF
)
check_equal "every fixture graph answers the picker" 0 "$BROKE"

TANGLED=$("$PY" - <<'PYEOF'
from {{ package_name }}.corpus import tangles
from {{ package_name }}.cycle import cycle
from {{ package_name }}.order import OrderError, order

refused = 0
for graph in tangles():
    if cycle(graph) is None:
        continue
    try:
        order(graph)
    except OrderError:
        refused += 1
print(refused)
PYEOF
)
check_equal "every shipped tangle refuses the listing" 3 "$TANGLED"

# --- the stories and the promises -------------------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
