#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }
run() { set +e; OUT=$("$@" 2>&1); STATUS=$?; set -e; }

echo "smoke: {{ npm_name }}"

run rake test
if [ "$STATUS" -eq 0 ]; then ok "test suite passes"; else bad "test suite passes"; printf '%s\n' "$OUT" | tail -8; fi

mkdir -p /tmp/scratchpad/rubyi18n/locales
cat > /tmp/scratchpad/rubyi18n/locales/en.yml <<'YAML'
en:
  greeting: Hello
YAML
cat > /tmp/scratchpad/rubyi18n/locales/de.yml <<'YAML'
de:
  greeting: Hallo
YAML

run bin/{{ npm_name }} greeting -l de -d /tmp/scratchpad/rubyi18n/locales
if [ "$STATUS" -eq 0 ]; then ok "resolve exits 0"; else bad "resolve exits 0"; fi
case "$OUT" in
  Hallo) ok "resolved value" ;; *) bad "resolved value"; printf ' got: %s\n' "$OUT" ;;
esac

run bin/{{ npm_name }} --check de -d /tmp/scratchpad/rubyi18n/locales
if [ "$STATUS" -eq 0 ]; then ok "check passes"; else bad "check passes"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
