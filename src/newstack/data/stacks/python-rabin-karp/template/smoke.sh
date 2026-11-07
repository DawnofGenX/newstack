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

# --- the scan, the count, and the digest ------------------------------------------
run "$PY" -m "$MODULE" find --pattern ana "banana"
check_equal "a find exits zero" 0 "$STATUS"
check_contains "the overlap starts twice" "starts     [1, 3]" "$OUT"
check_contains "the first is the leftmost" "first      1" "$OUT"

run "$PY" -m "$MODULE" count --pattern ana "banana"
check_equal "a count exits zero" 0 "$STATUS"
check_contains "the count sees the overlap" "count      2" "$OUT"

run "$PY" -m "$MODULE" find --pattern zzz "banana"
check_equal "an absent pattern exits one" 1 "$STATUS"
check_contains "the absence is named" "first      None" "$OUT"

run "$PY" -m "$MODULE" digest --pattern ana --json
WANT=$("$PY" - <<'PYEOF'
from {{ package_name }}.hashing import window_hash

print(window_hash("ana"))
PYEOF
)
DIGEST=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["digest"])' "$OUT")
check_equal "the digest is the documented weigh" "$WANT" "$DIGEST"

# --- the edges the gate refuses ---------------------------------------------------
run "$PY" -m "$MODULE" count --pattern "" "abra"
check_equal "the empty pattern exits zero" 0 "$STATUS"
check_contains "the empty pattern sits everywhere" "count      5" "$OUT"

run "$PY" -m "$MODULE" find --pattern abracadabra "a"
check_equal "a long pattern never sits" 1 "$STATUS"

run "$PY" -m "$MODULE" find --pattern Abra "abra"
check_equal "an uppercase pattern is unusable" 2 "$STATUS"
check_contains "the pattern is named" "not a pattern" "$OUT"

run "$PY" -m "$MODULE" find --pattern a "a b"
check_equal "a spaced text is unusable" 2 "$STATUS"
check_contains "the text is named" "not a text" "$OUT"

# --- the fixture corpus, naive-equal ----------------------------------------------
COUNT=$(grep -cvE '^[[:space:]]*(#|$)' fixtures/patterns.txt)
if [[ "$COUNT" -ge 12 ]]; then
  ok "the fixture holds a corpus ($COUNT patterns)"
else
  bad "the fixture is too small ($COUNT patterns)"
fi

BROKE=$("$PY" - <<'PYEOF'
import sys
from {{ package_name }}.naive import naive_starts
from {{ package_name }}.scanner import scan_starts

text = "abracadabracabanabracadabra"
broken = []
with open("fixtures/patterns.txt", encoding="utf-8") as handle:
    for line in handle:
        pattern = line.strip()
        if not pattern or pattern.startswith("#"):
            continue
        if scan_starts(text, pattern) != naive_starts(text, pattern):
            broken.append(pattern)
print(len(broken))
PYEOF
)
check_equal "every fixture pattern answers like the naive scan" 0 "$BROKE"

ROLLED=$("$PY" - <<'PYEOF'
from {{ package_name }}.corpus import synthetic
from {{ package_name }}.scanner import RollingScanner

text = "abracadabracabanabracadabra"
faults = 0
for pattern in list(synthetic(24, seed=11)) + ["abra", "anana"]:
    faults += len(RollingScanner(pattern).audit(text))
print(faults)
PYEOF
)
check_equal "the roll equals the fresh weigh on shipped windows" 0 "$ROLLED"

# --- the stories and the invariants -------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
