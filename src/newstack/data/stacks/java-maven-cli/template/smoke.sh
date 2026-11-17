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

if ! command -v java >/dev/null 2>&1; then
  echo "smoke: java is missing (install java)"
  exit 1
fi
if ! command -v mvn >/dev/null 2>&1; then
  echo "smoke: mvn is missing (install maven)"
  exit 1
fi

echo "smoke: java-maven-cli"

run mvn -B verify
if [ "$STATUS" -eq 0 ]; then ok "mvn verify"; else bad "mvn verify"; printf '%s\n' "$OUT" | tail -8; fi

if [ -f target/{{ npm_name }}.jar ]; then
  ok "jar exists"

  run java -jar target/{{ npm_name }}.jar --help
  if [ "$STATUS" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; printf '%s\n' "$OUT" | tail -8; fi

  set +e
  java -jar target/{{ npm_name }}.jar --bogus >/dev/null 2>&1
  st=$?
  set -e
  if [ "$st" -eq 2 ]; then ok "usage error exits 2"; else bad "usage error exits 2"; fi
else
  bad "jar exists"
fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]