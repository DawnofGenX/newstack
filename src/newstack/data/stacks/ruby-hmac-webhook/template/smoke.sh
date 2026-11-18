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

if ! command -v ruby >/dev/null 2>&1; then
  echo "smoke: ruby is missing (install ruby)"
  exit 1
fi

echo "smoke: {{ npm_name }}"

run rake test
if [ "$STATUS" -eq 0 ]; then
  ok "test suite passes"
else
  bad "test suite passes"
  printf '%s\n' "$OUT" | tail -8
fi

run bin/{{ npm_name }} sign --secret whsec_dev --timestamp 1700000000 --payload hello
if [ "$STATUS" -eq 0 ]; then ok "sign exits 0"; else bad "sign exits 0"; fi
case "$OUT" in
  t=1700000000,v1=????????????????????????????????????????????????????????????????)
    ok "signature has the documented shape" ;;
  *)
    bad "signature has the documented shape"
    printf '       got: %s\n' "$OUT" ;;
esac

SIGNED=$OUT
run bin/{{ npm_name }} verify --secret whsec_dev --header "$SIGNED" --payload hello --now 1700000000
if [ "$STATUS" -eq 0 ]; then ok "fresh matching header accepted"; else bad "fresh matching header accepted"; fi

run bin/{{ npm_name }} verify --secret whsec_dev --header "$SIGNED" --payload hello --now 1700009999
if [ "$STATUS" -eq 1 ]; then ok "stale header rejected with 1"; else bad "stale header rejected with 1"; fi

TAMPERED=$(printf 't=1700000000,v1=%064d' 0)
run bin/{{ npm_name }} verify --secret whsec_dev --header "$TAMPERED" --payload hello --now 1700000000
if [ "$STATUS" -eq 1 ]; then ok "tampered header rejected with 1"; else bad "tampered header rejected with 1"; fi

run sh -c "printf 'hello' | bin/{{ npm_name }} sign --secret whsec_dev --timestamp 1700000000 --stdin"
SIGNED_STDIN=$OUT
run sh -c "printf 'hello' | bin/{{ npm_name }} verify --secret whsec_dev --header '$SIGNED_STDIN' --stdin --now 1700000000"
if [ "$STATUS" -eq 0 ]; then ok "stdin payload round trips"; else bad "stdin payload round trips"; fi

run bin/{{ npm_name }} --bogus
if [ "$STATUS" -eq 2 ]; then ok "bad usage exits 2"; else bad "bad usage exits 2"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
