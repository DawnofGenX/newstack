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

# --- the loop, the price, and the table -------------------------------------------------
run "$PY" -m "$MODULE" encode "mississippimississippi"
check_equal "an encode exits zero" 0 "$STATUS"
check_contains "the encode prices the letters" "letters    22" "$OUT"

BITS=$("$PY" -m "$MODULE" encode "mississippimississippi" --json | "$PY" -c 'import json,sys
print(json.loads(sys.stdin.read())["bits"])')
BACK=$("$PY" -m "$MODULE" decode "$BITS" "mississippimississippi" | "$PY" -c 'import sys
print(sys.stdin.read().split("text       ")[1].strip().strip(chr(39)))')
check_equal "the bits read back the letters sent" "mississippimississippi" "$BACK"

run "$PY" -m "$MODULE" frequencies "banana" --json
check_equal "a frequencies exits zero" 0 "$STATUS"
COUNTS=$("$PY" -c 'import json,sys
print(json.loads(sys.stdin.read()) == {"a": 3, "b": 1, "n": 2})' <<< "$OUT")
check_equal "the counts are the counts" "True" "$COUNTS"

run "$PY" -m "$MODULE" roundtrip "abracadabraabracadabra"
check_equal "a roundtrip exits zero" 0 "$STATUS"
check_contains "the loop closes" "closed     True" "$OUT"

run "$PY" -m "$MODULE" roundtrip "aaaaaaaaaabbbbcc" --json
check_equal "a json roundtrip exits zero" 0 "$STATUS"
CLOSED=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["closed"])' "$OUT")
check_equal "the json loop closes" "True" "$CLOSED"

# --- the edges the gate refuses ---------------------------------------------------------
run "$PY" -m "$MODULE" encode "Mississippi"
check_equal "an uppercase text is unusable" 2 "$STATUS"
check_contains "the text is named" "not a lowercase letter" "$OUT"

run "$PY" -m "$MODULE" encode "a b"
check_equal "a spaced text is unusable" 2 "$STATUS"

run "$PY" -m "$MODULE" report --corpus "$WORK/missing.txt"
check_equal "a missing corpus exits two" 2 "$STATUS"

# --- the fixture corpus, loop after loop -------------------------------------------------
COUNT=$(grep -cvE '^[[:space:]]*(#|$)' fixtures/corpora.txt)
if [[ "$COUNT" -ge 8 ]]; then
  ok "the fixture holds a corpus ($COUNT texts)"
else
  bad "the fixture is too small ($COUNT texts)"
fi

BROKE=$("$PY" - <<'PYEOF'
from {{ package_name }}.coder import decode, encode, size_report
from {{ package_name }}.corpus import load_texts
from {{ package_name }}.table import audit
from {{ package_name }}.tree import walk_table_agreement, build_tree
from {{ package_name }}.freq import tally

broken = []
for text in load_texts("fixtures/corpora.txt"):
    letters, spent, book = size_report(text)
    if decode(encode(text, book), book) != text or audit(book) or spent >= letters * 8:
        broken.append(text)
    if not walk_table_agreement(build_tree(tally(text)), book):
        broken.append(text)
print(len(broken))
PYEOF
)
check_equal "every fixture text loops, audits silent, pays under eight bits" 0 "$BROKE"

# --- the stories and the invariants -------------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
