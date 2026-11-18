#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

run() {
  set +e
  OUT=$("$@" 2>&1)
  STATUS=$?
  set -e
}

if ! command -v deno >/dev/null 2>&1; then
  echo "smoke: deno is missing (install deno)"
  exit 1
fi

echo "smoke: deno-cidr-cli"

run deno check main.ts
if [ "$STATUS" -eq 0 ]; then ok "typecheck passes"; else bad "typecheck passes"; printf '%s\n' "$OUT" | tail -8; fi

run deno task test
if [ "$STATUS" -eq 0 ]; then ok "test suite passes"; else bad "test suite passes"; printf '%s\n' "$OUT" | tail -8; fi

run ./bin/{{ npm_name }} --help
if [ "$STATUS" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; fi

got=$(printf '10.1.2.3/8\n' | ./bin/{{ npm_name }})
if [ "$got" = '10.0.0.0/8 network=10.0.0.0 broadcast=10.255.255.255 hosts=16777214' ]; then
  ok "table output"
else
  bad "table output"; printf '       got: %s\n' "$got"
fi

got=$(printf '10.0.0.0/8\n192.168.0.0/16\n' | ./bin/{{ npm_name }} --contains 192.168.4.4)
case "$got" in
  192.168.0.0/16*) ok "contains filter" ;;
  *) bad "contains filter"; printf '       got: %s\n' "$got" ;;
esac

set +e
printf '10.0.0.0/33\n' | ./bin/{{ npm_name }} >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 1 ]; then ok "bad block exits 1"; else bad "bad block exits 1"; fi

set +e
./bin/{{ npm_name }} --bogus >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 2 ]; then ok "bad usage exits 2"; else bad "bad usage exits 2"; fi

set +e
./bin/{{ npm_name }} does-not-exist.txt >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 1 ]; then ok "missing file exits 1"; else bad "missing file exits 1"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
