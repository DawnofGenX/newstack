#!/bin/sh
set -u
FAILED=0
PASSED=0
pass() { echo "ok: $1"; PASSED=$((PASSED + 1)); }
fail() { echo "FAIL: $1"; FAILED=$((FAILED + 1)); }

BIN=./{{ npm_name }}

if "$BIN" --help >/dev/null 2>&1; then pass "help"; else fail "help"; fi

out=$(printf '[server]\nhost = "localhost"\nport = 8080\n' | "$BIN")
exp='server.host = "localhost"
server.port = 8080'
if [ "$out" = "$exp" ]; then pass "flatten"; else echo "got: [$out]"; fail "flatten"; fi

set +e
"$BIN" --bogus >/dev/null 2>&1
rc=$?
set -e
if [ "$rc" -eq 2 ]; then pass "usage"; else fail "usage (rc=$rc)"; fi

set +e
"$BIN" /no/such/file >/dev/null 2>&1
rc=$?
set -e
if [ "$rc" -eq 1 ]; then pass "missing"; else fail "missing (rc=$rc)"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]