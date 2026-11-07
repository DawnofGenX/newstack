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

# --- the walk, the count, and the cycle ------------------------------------------------
run "$PY" -m "$MODULE" distances 1 2 3 4 "1>2=4" "2>3=-2" "3>4=3" "1>3=5" "2>4=1" --source 1
check_equal "a walk exits zero" 0 "$STATUS"
check_contains "the walk counts the nodes" "nodes      4" "$OUT"
check_contains "the negative leg answers" "distance   3 2" "$OUT"

run "$PY" -m "$MODULE" distances 1 2 3 "1>2=-5" "2>3=2" --source 1 --json
check_equal "a json walk exits zero" 0 "$STATUS"
check_contains "the json answers the map" '{"1": 0, "2": -5, "3": -3}' "$OUT"

run "$PY" -m "$MODULE" cycles 0 1 2 3 "0>1=-2" "1>2=1" "2>0=0" "2>3=4" --source 0
check_equal "a cycle answer exits zero" 0 "$STATUS"
check_contains "the cycle is named" "cycle      [0, 1, 2]" "$OUT"

run "$PY" -m "$MODULE" distances 0 1 2 "0>1=-3" "1>2=-3" --source 0
check_contains "a chain settles" "distance   2 -6" "$OUT"

run "$PY" -m "$MODULE" distances 3 8 --source 3
check_contains "an unreachable node answers" "distance   8 unreached" "$OUT"

# --- the edges the door refuses ------------------------------------------------------------
run "$PY" -m "$MODULE" distances a b --source 1
check_equal "a word is not a graph" 2 "$STATUS"
check_contains "the token is named" "no integer label" "$OUT"

run "$PY" -m "$MODULE" distances 1.5
check_equal "a float is not a label" 2 "$STATUS"

run "$PY" -m "$MODULE" report --corpus "$WORK/missing.txt"
check_equal "a missing corpus exits two" 2 "$STATUS"

# --- the fixture corpus, walk after walk ----------------------------------------------------
COUNT=$(grep -cvE '^[[:space:]]*(#|$)' fixtures/graphs.txt)
if [[ "$COUNT" -ge 8 ]]; then
  ok "the fixture holds a corpus ($COUNT graphs)"
else
  bad "the fixture is too small ($COUNT graphs)"
fi

BROKE=$("$PY" - <<'PYEOF'
from {{ package_name }}.corpus import load_graphs
from {{ package_name }}.oracle import oracle_distances
from {{ package_name }}.walk import distances, settled

broken = []
for graph in load_graphs("fixtures/graphs.txt"):
    source = graph.nodes()[0]
    if distances(graph, source) != oracle_distances(graph, source) or settled(graph, source):
        broken.append(graph.to_text())
print(len(broken))
PYEOF
)
check_equal "every fixture graph agrees with the count" 0 "$BROKE"

# --- the stories and the promises -------------------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
