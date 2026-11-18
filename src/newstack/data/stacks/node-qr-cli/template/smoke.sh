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

for tool in node npm; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "smoke: $tool is missing (install $tool)"
    exit 1
  fi
done

echo "smoke: node-qr-cli"

run npm test
if [ "$STATUS" -eq 0 ]; then ok "tests pass"; else bad "tests pass"; printf '%s\n' "$OUT" | tail -8; fi

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

set +e
node src/cli.js --text "smoke" --output "$work/qr.png" >"$work/gen.log" 2>&1
rc=$?
set -e
if [ "$rc" -eq 0 ] && [ -s "$work/qr.png" ]; then
  ok "qr png generated"
else
  bad "qr png generated"
  cat "$work/gen.log" >&2 || true
fi

set +e
node -e "const fs=require('fs');const b=fs.readFileSync(process.argv[1]);if(!(b[0]===0x89&&b[1]===0x50&&b[2]===0x4e&&b[3]===0x47))process.exit(1);if(b.length<100)process.exit(1);" "$work/qr.png"
rc=$?
set -e
if [ "$rc" -eq 0 ]; then ok "png magic bytes and size"; else bad "png magic bytes and size"; fi

set +e
node src/cli.js --text "smoke" >"$work/term.log" 2>&1
rc=$?
set -e
if [ "$rc" -eq 0 ] && [ -s "$work/term.log" ]; then ok "terminal renderer runs"; else bad "terminal renderer runs"; cat "$work/term.log" >&2 || true; fi

rm -rf "$work"
trap - EXIT

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]