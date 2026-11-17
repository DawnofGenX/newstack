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

if ! command -v groovy >/dev/null 2>&1; then
  echo "smoke: groovy is missing (install groovy)"
  exit 1
fi

echo "smoke: groovy-cli"

run groovy -cp src:tests tests/run_tests.groovy
if [ "$STATUS" -eq 0 ]; then ok "groovy tests pass"; else bad "groovy tests pass"; printf '%s\n' "$OUT" | tail -8; fi

run sh -c "./bin/{{ npm_name }} --help | grep -qF 'Usage: {{ npm_name }} [OPTION]... [FILE]...'"
if [ "$STATUS" -eq 0 ]; then ok "help output"; else bad "help output"; printf '%s\n' "$OUT" | tail -8; fi

set +e
./bin/{{ npm_name }} --bogus >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 2 ]; then ok "usage error exits 2"; else bad "usage error exits 2"; fi

set +e
./bin/{{ npm_name }} /nonexistent/file.txt >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 1 ]; then ok "missing file exits 1"; else bad "missing file exits 1"; fi

run sh -c "test \"\$(printf 'alpha beta\\ngamma\\n' | ./bin/{{ npm_name }} -w)\" = '3' && test \"\$(printf 'alpha beta\\ngamma\\n' | ./bin/{{ npm_name }} -w -)\" = '3 -' && test \"\$(printf 'alpha beta\\ngamma delta\\n' | ./bin/{{ npm_name }})\" = '      2       4      23'"
if [ "$STATUS" -eq 0 ]; then ok "stdin handling"; else bad "stdin handling"; printf '%s\n' "$OUT" | tail -8; fi

run sh -c 'mkdir -p .parity
printf "alpha beta\ngamma delta\n" > .parity/p1.txt
printf "alpha beta\ngamma" > .parity/p2.txt
printf "h\303\251llo w\303\266rld\n" > .parity/p3.txt
: > .parity/p4.txt
printf "a\tb\vc\fd\n" > .parity/p5.txt
for file in .parity/p*.txt; do
  ours=$(./bin/{{ npm_name }} "$file" | awk "{print \$1, \$2, \$3}")
  theirs=$(wc -l -w -c < "$file" | awk "{print \$1, \$2, \$3}")
  test "$ours" = "$theirs"
done
rm -rf .parity'
if [ "$STATUS" -eq 0 ]; then ok "parity with wc"; else bad "parity with wc"; printf '%s\n' "$OUT" | tail -8; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]