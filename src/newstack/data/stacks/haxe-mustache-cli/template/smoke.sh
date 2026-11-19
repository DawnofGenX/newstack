#!/bin/sh
set -u

PASSED=0
FAILED=0
ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }
run() { set +e; OUT=$("$@" 2>&1); STATUS=$?; set -e; }

if ! command -v haxe >/dev/null 2>&1; then echo "smoke: haxe is missing"; exit 1; fi
if ! command -v neko >/dev/null 2>&1; then echo "smoke: neko is missing"; exit 1; fi

echo "smoke: haxe-mustache-cli"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

run sh -c 'make build'
if [ "$STATUS" -eq 0 ]; then ok "build"; else bad "build"; printf '%s\n' "$OUT" | tail -8; fi

run sh -c 'make test'
if [ "$STATUS" -eq 0 ]; then ok "test"; else bad "test"; printf '%s\n' "$OUT" | tail -8; fi

run ./bin/{{ npm_name }} --help
if [ "$STATUS" -eq 0 ]; then ok "help"; else bad "help"; printf '%s\n' "$OUT" | tail -8; fi

run sh -c './bin/{{ npm_name }} --bogus >/dev/null 2>&1; test $? -eq 2'
if [ "$STATUS" -eq 0 ]; then ok "usage-error"; else bad "usage-error"; fi

run sh -c './bin/{{ npm_name }} /no/such/file >/dev/null 2>&1; test $? -eq 1'
if [ "$STATUS" -eq 0 ]; then ok "missing-file"; else bad "missing-file"; fi

printf 'Hello {{!name}}\n' > "$work/t.mst"
printf '{"name":"world"}' > "$work/d.json"
run sh -c "./bin/{{ npm_name }} $work/t.mst $work/d.json"
if [ "$STATUS" -eq 0 ] && [ "$OUT" = "Hello world" ]; then ok "render"; else bad "render"; printf 'got: [%s]\n' "$OUT"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
