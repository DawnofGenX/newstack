#!/bin/sh
set -eu
FAILED=0
PASS=0
check() { if "$@" >/dev/null 2>&1; then PASS=$((PASS+1)); else FAILED=$((FAILED+1)); echo "FAIL: $*"; fi; }
check crystal spec
check mkdir -p bin
check crystal build -o bin/{{ npm_name }} src/main.cr
printf 'name = "demo"\n[server]\nport = 8080\n' > /tmp/c.toml
check ./bin/{{ npm_name }} /tmp/c.toml
check sh -c './bin/{{ npm_name }} /tmp/c.toml | grep -q "server.port = 8080"'
check ./bin/{{ npm_name }} --help
check sh -c './bin/{{ npm_name }} --bogus >/dev/null 2>&1; test $? -eq 2'
check sh -c './bin/{{ npm_name }} nope.toml >/dev/null 2>&1; test $? -eq 1'
printf 'smoke: %d passed, %d failed\n' "$PASS" "$FAILED"
[ "$FAILED" -eq 0 ]
