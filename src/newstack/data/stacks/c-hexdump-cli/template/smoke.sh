#!/bin/sh
set -u
FAILED=0
PASSED=0
pass() { echo "ok: $1"; PASSED=$((PASSED + 1)); }
fail() { echo "FAIL: $1"; FAILED=$((FAILED + 1)); }

BIN=./build/c-hexdump-cli

if "$BIN" --help >/dev/null 2>&1; then pass "help"; else fail "help"; fi

out=$(printf 'Hello\n' | "$BIN")
exp='00000000  48 65 6c 6c 6f 0a                                 |Hello.          |'
if [ "$out" = "$exp" ]; then pass "hex"; else echo "got: [$out]"; fail "hex"; fi

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