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

if ! command -v ansible-playbook >/dev/null 2>&1; then
  echo "smoke: ansible-playbook is missing (install ansible)"
  exit 1
fi

echo "smoke: ansible-role"

run ansible-playbook --syntax-check -i localhost, tests/playbook.yml
if [ "$STATUS" -eq 0 ]; then ok "syntax check passes"; else bad "syntax check passes"; printf '%s\n' "$OUT" | tail -8; fi

rm -rf .play
mkdir -p .play
run ansible-playbook -i localhost, -e "textstat_prefix=$PWD/.play/prefix" tests/playbook.yml
if [ "$STATUS" -eq 0 ]; then ok "apply passes"; else bad "apply passes"; printf '%s\n' "$OUT" | tail -8; fi

run ansible-playbook -i localhost, -e "textstat_prefix=$PWD/.play/prefix" tests/verify.yml
if [ "$STATUS" -eq 0 ]; then ok "verify-state passes"; else bad "verify-state passes"; printf '%s\n' "$OUT" | tail -8; fi

# counter test
mkdir -p .play
printf 'alpha beta\ngamma\n' > .play/sample.txt
got=$(.play/prefix/bin/textstat .play/sample.txt)
if [ "$got" = '2 3 17' ]; then ok "counter output"; else bad "counter output"; printf '       got: %s\n' "$got"; fi

# idempotent rerun
run ansible-playbook -i localhost, -e "textstat_prefix=$PWD/.play/prefix" tests/playbook.yml
if printf '%s\n' "$OUT" | grep -q 'changed=0'; then ok "idempotent rerun"; else bad "idempotent rerun"; fi

rm -rf .play

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]