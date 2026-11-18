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

echo "smoke: deno-diff-cli"

run deno check main.ts
if [ "$STATUS" -eq 0 ]; then ok "typecheck passes"; else bad "typecheck passes"; printf '%s\n' "$OUT" | tail -8; fi

run deno task test
if [ "$STATUS" -eq 0 ]; then ok "test suite passes"; else bad "test suite passes"; printf '%s\n' "$OUT" | tail -8; fi

run ./bin/{{ npm_name }} --help
if [ "$STATUS" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; fi

tmp=$(mktemp -d)
printf 'one\ntwo\nthree\n' > "$tmp/a.txt"
printf 'one\nTWO\nthree\n' > "$tmp/b.txt"

got=$(./bin/{{ npm_name }} -U 0 "$tmp/a.txt" "$tmp/b.txt" | tr '\n' '|')
if [ "$got" = "--- $tmp/a.txt|+++ $tmp/b.txt|@@ -2 +2 @@|-two|+TWO|" ]; then
  ok "unified diff"
else
  bad "unified diff"; printf '       got: %s\n' "$got"
fi

got=$(./bin/{{ npm_name }} --stat "$tmp/a.txt" "$tmp/b.txt")
if [ "$got" = "$tmp/a.txt -> $tmp/b.txt: 1 insertion(s), 1 deletion(s), 2 change(s)" ]; then
  ok "stat output"
else
  bad "stat output"; printf '       got: %s\n' "$got"
fi

got=$(./bin/{{ npm_name }} -q "$tmp/a.txt" "$tmp/a.txt")
if [ -z "$got" ]; then ok "identical files print nothing"; else bad "identical files print nothing"; fi

set +e
./bin/{{ npm_name }} --exit-code "$tmp/a.txt" "$tmp/b.txt" >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 1 ]; then ok "differences exit 1 with --exit-code"; else bad "differences exit 1 with --exit-code"; fi

set +e
./bin/{{ npm_name }} "$tmp/a.txt" "$tmp/missing.txt" >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 1 ]; then ok "missing file exits 1"; else bad "missing file exits 1"; fi

set +e
./bin/{{ npm_name }} --bogus "$tmp/a.txt" "$tmp/b.txt" >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 2 ]; then ok "bad usage exits 2"; else bad "bad usage exits 2"; fi

rm -rf "$tmp"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
