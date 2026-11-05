#!/usr/bin/env bash
# The pool's contract, checked from the outside: reuse, a free event loop, a moved buffer,
# a bounded queue, a replacement after a crash, and a close that drains.
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
contains "--version names the program" "$PROGRAM 0.1.0" "$out"

out=$("$NODE" dist/src/main.js --help 2>&1)
contains "help lists bench" "bench" "$out"
contains "help lists demo" "demo" "$out"
contains "help states the exit codes" "1 the pool broke its own contract" "$out"

out=$("$NODE" dist/src/main.js bench --size 2 --tasks 16 2>&1)
status=$?
[ "$status" -eq 0 ] && ok "bench exits 0" || bad "bench exits 0 (got $status)"
contains "bench reports its workers" "workers    2" "$out"
contains "bench completes the tasks" "completed  16" "$out"
contains "bench spawns no more than its size" "spawns     2" "$out"
contains "bench keeps the contract" "contract   kept" "$out"
contains "bench sums what it ran" "sum        136" "$out"

out=$("$NODE" dist/src/main.js bench --size 0 2>&1)
status=$?
[ "$status" -eq 2 ] && ok "a zero size exits 2" || bad "a zero size exits 2 (got $status)"

out=$("$NODE" dist/src/main.js bench --tasks many 2>&1)
status=$?
[ "$status" -eq 2 ] && ok "a non-integer exits 2" || bad "a non-integer exits 2 (got $status)"

out=$("$NODE" dist/src/main.js bench --tasks 2>&1)
status=$?
[ "$status" -eq 2 ] && ok "a missing value exits 2" || bad "a missing value exits 2 (got $status)"

out=$("$NODE" dist/src/main.js nope 2>&1)
status=$?
[ "$status" -eq 2 ] && ok "an unknown command exits 2" || bad "an unknown command exits 2 (got $status)"

out=$("$NODE" dist/src/main.js demo 2>&1)
status=$?
[ "$status" -eq 0 ] && ok "demo exits 0" || bad "demo exits 0 (got $status)"
contains "demo shows reuse" "a pool spawns once" "$out"
contains "demo shows the free loop" "the same 180 ms on the main thread: 0 ticks" "$out"
contains "demo shows the detached buffer" "after it: 0.0 KiB on the sender" "$out"
contains "demo shows the bounded queue" "refused: the queue holds 2 task(s)" "$out"
contains "demo shows the crash" "the worker exited with code 7 before answering" "$out"
contains "demo shows the drain" "close report:" "$out"
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
