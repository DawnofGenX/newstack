#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

if ! command -v haxe >/dev/null 2>&1; then echo "smoke: haxe is missing"; exit 1; fi
if ! command -v neko >/dev/null 2>&1; then echo "smoke: neko is missing"; exit 1; fi

echo "smoke: haxe-csv-lite"

if (haxe build.hxml && haxe test.hxml); then ok "build"; else bad "build"; fi
if (neko build/tests.n); then ok "test"; else bad "test"; fi
if (printf 'name,age\nalice,30\n' > /tmp/haxe-csv.csv && test "$(./bin/{{ npm_name }} --count /tmp/haxe-csv.csv)" = "1"); then ok "count"; else bad "count"; fi
if (set +e; ./bin/{{ npm_name }} --bogus >/dev/null 2>&1; status=$?; test "$status" -eq 2); then ok "usage-error"; else bad "usage-error"; fi
if (set +e; ./bin/{{ npm_name }} /nonexistent.csv >/dev/null 2>&1; status=$?; test "$status" -eq 1); then ok "missing-file"; else bad "missing-file"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
