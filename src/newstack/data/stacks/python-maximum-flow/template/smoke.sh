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

# --- the value, the map, and the enumeration ----------------------------------------------
run "$PY" -m "$MODULE" flow 0 3 "0>1=3" "1>3=2" "0>2=2" "2>3=3" "0>3=1" "1>2=1"
check_equal "a flow exits zero" 0 "$STATUS"
check_contains "the value is the least cut" "flow       6" "$OUT"

run "$PY" -m "$MODULE" flow 0 3 --json "0>1=3" "1>3=2" "0>2=2" "2>3=3" "0>3=1" "1>2=1"
check_equal "a json flow exits zero" 0 "$STATUS"
check_contains "the json carries the value" '"flow": 6' "$OUT"

run "$PY" -m "$MODULE" map 0 3 "0>1=3" "1>3=2" "0>2=2" "2>3=3" "0>3=1" "1>2=1"
check_equal "a map exits zero" 0 "$STATUS"
check_contains "the map ships along the diamond" "0->1 ships 3" "$OUT"

run "$PY" -m "$MODULE" map 0 3 --json "0>1=3" "1>3=2" "0>2=2" "2>3=3" "0>3=1" "1>2=1"
check_equal "a json map exits zero" 0 "$STATUS"
check_contains "the json carries an arc" '"arc": [0, 1]' "$OUT"

run "$PY" -m "$MODULE" flow 0 3 "0>1=4" "1>2=2" "2>3=6"
check_equal "a chain flow exits zero" 0 "$STATUS"
check_contains "the chain carries its least door" "flow       2" "$OUT"

# --- the arcs the door refuses ---------------------------------------------------------------
run "$PY" -m "$MODULE" flow 0 3 a b
check_equal "a word is not a network" 2 "$STATUS"
check_contains "the token is named" "no integer label" "$OUT"

run "$PY" -m "$MODULE" flow 0 3 "0>1=2" "1>0=2"
check_equal "a two-way channel is refused" 2 "$STATUS"

run "$PY" -m "$MODULE" flow 0 3 0 1 "1>0"
check_equal "a capacityless arc is refused" 2 "$STATUS"

run "$PY" -m "$MODULE" report --corpus "$WORK/missing.txt"
check_equal "a missing corpus exits two" 2 "$STATUS"

run "$PY" -m "$MODULE" flow 0 0 "0>1=1"
check_equal "ends that match are refused" 2 "$STATUS"

# --- the fixture corpus, walked network after network -----------------------------------------
COUNT=$(grep -cvE '^[[:space:]]*(#|$)' fixtures/networks.txt)
if [[ "$COUNT" -ge 8 ]]; then
  ok "the fixture holds a corpus ($COUNT networks)"
else
  bad "the fixture is too small ($COUNT networks)"
fi

BROKE=$("$PY" - <<'PYEOF'
from {{ package_name }}.corpus import load_graphs
from {{ package_name }}.oracle import min_cut
from {{ package_name }}.solve import audit, flow_map, max_flow

broken = []
for graph in load_graphs("fixtures/networks.txt"):
    source, sink = min(graph.nodes()), max(graph.nodes())
    shipped = flow_map(graph, source, sink)
    if max_flow(graph, source, sink) != min_cut(graph, source, sink):
        broken.append(graph.to_text())
        continue
    if audit(graph, source, sink, shipped):
        broken.append(graph.to_text())
print(len(broken))
PYEOF
)
check_equal "every fixture network agrees with the enumeration" 0 "$BROKE"

# --- the stories and the promises ---------------------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
