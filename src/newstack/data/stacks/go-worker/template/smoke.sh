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
  echo "smoke: go is missing (install go)"
  exit 1
fi
if ! command -v make >/dev/null 2>&1; then
  echo "smoke: make is missing (install make)"
  exit 1
fi
if ! command -v bash >/dev/null 2>&1; then
  echo "smoke: bash is missing (install bash)"
  exit 1
fi

echo "smoke: go-worker"

run go vet ./...
if [ "$STATUS" -eq 0 ]; then ok "go vet passes"; else bad "go vet passes"; printf '%s\n' "$OUT" | tail -8; fi

run go test ./...
if [ "$STATUS" -eq 0 ]; then ok "go test passes"; else bad "go test passes"; printf '%s\n' "$OUT" | tail -8; fi

run make build
if [ "$STATUS" -eq 0 ]; then ok "make build"; else bad "make build"; printf '%s\n' "$OUT" | tail -8; fi

if [ -x ./bin/{{ npm_name }} ]; then
  run ./bin/{{ npm_name }} --selftest
  if [ "$STATUS" -eq 0 ]; then ok "selftest passes"; else bad "selftest passes"; printf '%s\n' "$OUT" | tail -8; fi
else
  bad "built binary exists"
fi

run bash run.sh
if [ "$STATUS" -eq 0 ]; then ok "worker job run"; else bad "worker job run"; printf '%s\n' "$OUT" | tail -8; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]