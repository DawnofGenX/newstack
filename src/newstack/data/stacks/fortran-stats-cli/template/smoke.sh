#!/bin/sh
set -u
FAILED=0
PASSED=0
pass() { echo "ok: $1"; PASSED=$((PASSED + 1)); }
fail() { echo "FAIL: $1"; FAILED=$((FAILED + 1)); }

BIN=./bin/{{ npm_name }}

if "$BIN" --help >/dev/null 2>&1; then pass "help"; else fail "help"; fi

out=$(printf '1 2 3 4\n' | "$BIN")
case "$out" in
  *"mean:"*) pass "stats";;
  *) echo "got: [$out]"; fail "stats";;
esac

set +e
"$BIN" --bogus >/dev/null 2>&1
rc=$?
set -e
if [ "$rc" -eq 2 ]; then pass "usage"; else fail "usage (rc=$rc)"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]