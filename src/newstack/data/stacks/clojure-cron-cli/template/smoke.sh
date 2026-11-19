#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

check() {
  if [ "$2" = "$3" ]; then ok "$1"; else bad "$1"; printf '       expected: %s\n       actual:   %s\n' "$2" "$3"; fi
}

if ! command -v clojure >/dev/null 2>&1; then
  echo "smoke: clojure is missing (install clojure)"
  exit 1
fi
if ! command -v java >/dev/null 2>&1; then
  echo "smoke: java is missing (install java)"
  exit 1
fi

echo "smoke: {{ package_name }}"

set +e
clojure -M -e "(require 'cronkit.cli)" >/dev/null 2>&1
ST=$?
set -e
if [ "$ST" -eq 0 ]; then ok "namespaces load"; else bad "namespaces load"; fi

set +e
clojure -M:test -m cronkit.run-tests >/dev/null 2>&1
ST=$?
set -e
if [ "$ST" -eq 0 ]; then ok "test suite passes"; else bad "test suite passes"; fi

check "help exits 0" "0" "$(sh -c "./bin/{{ npm_name }} --help >/dev/null; echo \$?")"
check "version" "0.1.0" "$(./bin/{{ npm_name }} --version)"
check "next runs" "2024-01-01T00:15:00Z" "$(./bin/{{ npm_name }} -n 1 --from 2024-01-01T00:00:00Z '*/15 * * * *')"
check "weekday schedule" "2024-01-08T09:00:00Z" "$(./bin/{{ npm_name }} -n 1 --from 2024-01-05T10:00:00Z '0 9 * * 1-5')"
check "explain prints the fields" "expression  : 0 9 * * 1-5" "$(./bin/{{ npm_name }} --explain -n 1 --from 2024-01-01T00:00:00Z '0 9 * * 1-5' | head -1)"
check "usage error exits 2" "2" "$(sh -c "./bin/{{ npm_name }} --bogus 2>/dev/null; echo \$?")"
check "bad field exits 2" "2" "$(sh -c "./bin/{{ npm_name }} '61 * * * *' 2>/dev/null; echo \$?")"
check "impossible date exits 1" "1" "$(sh -c "./bin/{{ npm_name }} '0 0 31 2 *' 2>/dev/null; echo \$?")"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
