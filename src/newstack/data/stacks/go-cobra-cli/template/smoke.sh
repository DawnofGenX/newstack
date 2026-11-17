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

if ! command -v go >/dev/null 2>&1; then
  echo "smoke: go is missing"
  exit 1
fi

echo "smoke: go-cobra-cli"

run go vet ./...
if [ "$STATUS" -eq 0 ]; then ok "go vet passes"; else bad "go vet passes"; printf '%s\n' "$OUT" | tail -8; fi

run go test ./...
if [ "$STATUS" -eq 0 ]; then ok "go test passes"; else bad "go test passes"; printf '%s\n' "$OUT" | tail -8; fi

run go build -o bin/app .
if [ "$STATUS" -eq 0 ]; then ok "go build"; else bad "go build"; printf '%s\n' "$OUT" | tail -8; fi

if [ -x ./bin/app ]; then
  got=$(./bin/app greet smoke)
  if [ "$got" = 'Hello, smoke!' ]; then ok "binary greets smoke"; else bad "binary greets smoke"; printf '       got: %s\n' "$got"; fi

  got=$(./bin/app add 4 7)
  if [ "$got" = '11' ]; then ok "binary adds"; else bad "binary adds"; printf '       got: %s\n' "$got"; fi

  got=$(./bin/app --version)
  if echo "$got" | grep -q "0.1.0"; then ok "binary version"; else bad "binary version"; printf '       got: %s\n' "$got"; fi
else
  bad "binary exists"
fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]