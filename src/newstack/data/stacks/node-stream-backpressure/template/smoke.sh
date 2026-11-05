#!/usr/bin/env bash
# The claim from the outside: the same bytes, four producers, and only the two that wait
# for drain keep the buffer near one chunk.
set -uo pipefail
cd "$(dirname "$0")"

NODE=${NODE:-node}
passed=0
failed=0

ok() {
  passed=$((passed + 1))
  printf 'ok   %s\n' "$1"
}

bad() {
  failed=$((failed + 1))
  printf 'FAIL %s\n' "$1"
}

contains() {
  local name=$1 needle=$2 haystack=$3
  case "$haystack" in
    *"$needle"*) ok "$name" ;;
    *) bad "$name (no '$needle')" ;;
  esac
}

absent() {
  local name=$1 needle=$2 haystack=$3
  case "$haystack" in
    *"$needle"*) bad "$name (found '$needle')" ;;
    *) ok "$name" ;;
  esac
}

if npm run build >build.log 2>&1; then
  ok "the project builds"
else
  bad "the project builds"
  tail -20 build.log
  printf '\n%s passed, %s failed\n' "$passed" "$failed"
  exit 1
fi

PROGRAM=$("$NODE" -p 'require("./package.json").name')

out=$("$NODE" dist/src/main.js --version 2>&1)
status=$?
[ "$status" -eq 0 ] && ok "--version exits 0" || bad "--version exits 0 (got $status)"
contains "--version names the program" "$PROGRAM" "$out"
contains "--version carries a version" "$PROGRAM 0.1.0" "$out"

out=$("$NODE" dist/src/main.js --help 2>&1)
contains "help lists compare" "compare" "$out"
contains "help lists demo" "demo" "$out"
contains "help states the exit codes" "1 a buffer bound was breached" "$out"

out=$("$NODE" dist/src/main.js compare --chunks 128 --latency 1 2>&1)
status=$?
[ "$status" -eq 0 ] && ok "compare exits 0" || bad "compare exits 0 (got $status)"
contains "compare names the ignoring mode" "ignoring" "$out"
contains "compare names the awaiting mode" "awaiting" "$out"
contains "compare names the honoring mode" "honoring" "$out"
contains "compare reports a bounded peak" "bounded    yes" "$out"
contains "compare delivers the whole series" "delivered 2048.0 KiB" "$out"

# 128 chunks of 16 KiB is 2 MiB: a producer that ignores the refusal buffers all of it,
# which is 128 chunks' worth of a 16 KiB highWaterMark.
case "$out" in
  *"2048.0 KiB  (128.0x a chunk)"*) ok "ignoring buffers the whole series" ;;
  *) bad "ignoring buffers the whole series" ;;
esac

out=$("$NODE" dist/src/main.js compare --chunks 128 --latency 1 --max-peak-chunks 0 2>&1)
status=$?
[ "$status" -eq 1 ] && ok "an impossible bound exits 1" || bad "an impossible bound exits 1 (got $status)"
contains "the breach is named" "bounded    NO" "$out"

out=$("$NODE" dist/src/main.js compare --chunks 0 2>&1)
status=$?
[ "$status" -eq 2 ] && ok "zero chunks exits 2" || bad "zero chunks exits 2 (got $status)"

out=$("$NODE" dist/src/main.js compare --chunks many 2>&1)
status=$?
[ "$status" -eq 2 ] && ok "a non-integer exits 2" || bad "a non-integer exits 2 (got $status)"

out=$("$NODE" dist/src/main.js compare --chunks 2>&1)
status=$?
[ "$status" -eq 2 ] && ok "a missing value exits 2" || bad "a missing value exits 2 (got $status)"

out=$("$NODE" dist/src/main.js nope 2>&1)
status=$?
[ "$status" -eq 2 ] && ok "an unknown command exits 2" || bad "an unknown command exits 2 (got $status)"

out=$("$NODE" dist/src/main.js demo 2>&1)
status=$?
[ "$status" -eq 0 ] && ok "demo exits 0" || bad "demo exits 0 (got $status)"
contains "demo tells the refusal story" "a false return is a request, not an error" "$out"
contains "demo shows the await trap" "a promise that is already kept" "$out"
contains "demo shows the stuck transform" "settled=false, error=null" "$out"
contains "demo names the doubled callback" "Callback called multiple times" "$out"
absent "demo has no failing line" "FAIL " "$out"

out=$(npm run selftest 2>&1)
status=$?
[ "$status" -eq 0 ] && ok "selftest exits 0" || bad "selftest exits 0 (got $status)"
case "$out" in
  *"checks passed"*) ok "selftest reports its checks" ;;
  *) bad "selftest reports its checks" ;;
esac
absent "selftest reports no failure" "FAIL " "$out"

rm -f build.log
printf '\nsmoke: %s passed, %s failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ] || exit 1
