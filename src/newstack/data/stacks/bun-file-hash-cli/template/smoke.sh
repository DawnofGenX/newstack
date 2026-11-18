#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

if ! command -v bun >/dev/null 2>&1; then
  echo "smoke: bun is missing (install bun)"
  exit 1
fi

echo "smoke: {{ npm_name }}"

if bun test >/tmp/hashsum-test.log 2>&1; then ok "test suite passes"; else bad "test suite passes"; tail -8 /tmp/hashsum-test.log; fi

printf 'hello' > sample.txt

out=$(./bin/{{ npm_name }} sample.txt)
if [ "$out" = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824  sample.txt" ]; then
  ok "sha256 of hello"
else
  bad "sha256 of hello"
fi

out=$(./bin/{{ npm_name }} --algo crc32 sample.txt)
if [ "$out" = "3610a686  sample.txt" ]; then ok "crc32 of hello"; else bad "crc32 of hello"; fi

./bin/{{ npm_name }} sample.txt > SUMS
if ./bin/{{ npm_name }} --check SUMS | grep -q '1 ok, 0 failed'; then ok "check accepts a good checksum"; else bad "check accepts a good checksum"; fi

printf '00  sample.txt\n' > BADSUMS
set +e
./bin/{{ npm_name }} --check BADSUMS >/dev/null 2>&1
status=$?
set -e
if [ "$status" -eq 1 ]; then ok "check exits 1 on a mismatch"; else bad "check exits 1 on a mismatch"; fi

set +e
./bin/{{ npm_name }} --bogus >/dev/null 2>&1
status=$?
set -e
if [ "$status" -eq 2 ]; then ok "bad usage exits 2"; else bad "bad usage exits 2"; fi

rm -f sample.txt SUMS BADSUMS /tmp/hashsum-test.log

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
