#!/usr/bin/env bash
set -uo pipefail

PROG="./bin/{{ npm_name }}"
FAILED=0
PASSED=0

ok() { PASSED=$((PASSED + 1)); }
bad() { FAILED=$((FAILED + 1)); echo "FAIL: $*" >&2; }

bun test >/dev/null 2>&1
if [ $? -eq 0 ]; then ok; else bad "bun test"; fi

if "$PROG" --help >/dev/null 2>&1; then ok; else bad "--help"; fi

set +e
"$PROG" --bogus >/dev/null 2>&1
[ $? -eq 2 ] && ok || bad "usage error must exit 2"
set -e

out=$("$PROG" --root src '**/*.ts' 2>&1)
echo "$out" | grep -qx 'cli.ts' && ok || bad "did not find cli.ts: $out"
echo "$out" | grep -qx 'glob/glob.ts' && ok || bad "did not find glob/glob.ts: $out"

out=$("$PROG" --root src '*.ts' 2>&1)
[ "$out" = "cli.ts" ] && ok || bad "single-segment match: $out"

set +e
"$PROG" --root src '*.rs' >/dev/null 2>&1
[ $? -eq 1 ] && ok || bad "no match must exit 1"
set -e

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
