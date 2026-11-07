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

# --- the tree, the total, and the enumeration ---------------------------------------------
run "$PY" -m "$MODULE" tree 1 1 2 3 "1>2=4" "2>3=1" "1>3=1"
check_equal "a tree exits zero" 0 "$STATUS"
check_contains "the tree counts its edges" "edges      2" "$OUT"
check_contains "the tree carries the cheap pair" "2-3 at 1" "$OUT"

run "$PY" -m "$MODULE" tree 1 --json 1 2 3 "1>2=4" "2>3=1" "1>3=1"
check_equal "a json tree exits zero" 0 "$STATUS"
check_contains "the json answers the edge" '"edge": [1, 3]' "$OUT"

run "$PY" -m "$MODULE" cost 1 1 2 3 "1>2=4" "2>3=1" "1>3=1"
check_equal "a total exits zero" 0 "$STATUS"
check_contains "the total is the least" "cost       2" "$OUT"

run "$PY" -m "$MODULE" cost 1 --json 1 2 3 "1>2=4" "2>3=1" "1>3=1"
check_equal "a json total exits zero" 0 "$STATUS"
check_contains "the json carries the total" '"cost": 2' "$OUT"

run "$PY" -m "$MODULE" cost 1 1 2 3 4 "1>2=1" "2>3=1" "3>4=1" "1>4=9"
check_equal "a chain total exits zero" 0 "$STATUS"
check_contains "the chain spans for three" "cost       3" "$OUT"

# --- the edges the door refuses ------------------------------------------------------------
run "$PY" -m "$MODULE" tree 1 a b
check_equal "a word is not a graph" 2 "$STATUS"
check_contains "the token is named" "no integer label" "$OUT"

run "$PY" -m "$MODULE" tree 1 1.5
check_equal "a float is not a label" 2 "$STATUS"

run "$PY" -m "$MODULE" tree 1 1 2 "1>2"
check_equal "a weightless edge is refused" 2 "$STATUS"

run "$PY" -m "$MODULE" report --corpus "$WORK/missing.txt"
check_equal "a missing corpus exits two" 2 "$STATUS"

run "$PY" -m "$MODULE" cost 1 1 2 7 "1>2=1"
check_equal "a graph in pieces exits two" 2 "$STATUS"

# --- the fixture corpus, grown graph after graph --------------------------------------------
COUNT=$(grep -cvE '^[[:space:]]*(#|$)' fixtures/graphs.txt)
if [[ "$COUNT" -ge 8 ]]; then
  ok "the fixture holds a corpus ($COUNT graphs)"
else
  bad "the fixture is too small ($COUNT graphs)"
fi

BROKE=$("$PY" - <<'PYEOF'
from {{ package_name }}.corpus import load_graphs
from {{ package_name }}.oracle import min_cost
from {{ package_name }}.solve import audit, spanning_tree, tree_cost

broken = []
for graph in load_graphs("fixtures/graphs.txt"):
    start = min(graph.nodes())
    edges = spanning_tree(graph, start)
    if tree_cost(graph, start) != min_cost(graph) or audit(graph, start, edges):
        broken.append(graph.to_text())
        continue
    if len(edges) != len(graph) - 1:
        broken.append(graph.to_text())
print(len(broken))
PYEOF
)
check_equal "every fixture graph agrees with the enumeration" 0 "$BROKE"

# --- the stories and the promises -------------------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
