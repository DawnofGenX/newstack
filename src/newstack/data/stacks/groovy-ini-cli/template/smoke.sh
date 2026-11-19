#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

if ! command -v groovy >/dev/null 2>&1; then echo "smoke: groovy is missing"; exit 1; fi

echo "smoke: groovy-ini-cli"

if (groovy -cp src:tests tests/run_tests.groovy); then ok "test"; else bad "test"; fi

if (./bin/{{ npm_name }} --help | grep -qF 'Usage: {{ npm_name }} [OPTION]... [FILE]...'); then ok "help"; else bad "help"; fi

if (set +e; ./bin/{{ npm_name }} --bogus >/dev/null 2>&1; status=$?; test "$status" -eq 2); then ok "usage-error"; else bad "usage-error"; fi

if (set +e; ./bin/{{ npm_name }} /nonexistent/file.ini >/dev/null 2>&1; status=$?; test "$status" -eq 1); then ok "missing-file"; else bad "missing-file"; fi

if (printf '[app]\ncount=42\n' > /tmp/groovy-ini-smoke.ini && test "$(./bin/{{ npm_name }} --get app.count /tmp/groovy-ini-smoke.ini)" = "42"); then ok "get"; else bad "get"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
