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

if ! command -v terraform >/dev/null 2>&1; then
  echo "smoke: terraform is missing (install terraform)"
  exit 1
fi

echo "smoke: terraform-module"

run terraform fmt -check -recursive
if [ "$STATUS" -eq 0 ]; then ok "terraform fmt"; else bad "terraform fmt"; fi

run terraform init -backend=false -input=false
if [ "$STATUS" -eq 0 ]; then ok "terraform init"; else bad "terraform init"; printf '%s\n' "$OUT" | tail -8; fi

run terraform validate
if [ "$STATUS" -eq 0 ]; then ok "terraform validate"; else bad "terraform validate"; printf '%s\n' "$OUT" | tail -8; fi

run terraform test
if [ "$STATUS" -eq 0 ]; then ok "terraform test"; else bad "terraform test"; printf '%s\n' "$OUT" | tail -12; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]