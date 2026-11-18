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

echo "smoke: node-markdown-site"

run npm test
if [ "$STATUS" -eq 0 ]; then ok "tests pass"; else bad "tests pass"; printf '%s\n' "$OUT" | tail -8; fi

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/content"
cat > "$work/content/hello.md" <<'EOF'
---
title: Smoke Title
---
# Hello

Smoke body text.
EOF

set +e
OUT=$(node src/cli.js --input "$work/content" --output "$work/dist" 2>&1)
STATUS=$?
set -e
if [ "$STATUS" -eq 0 ]; then ok "build exits cleanly"; else bad "build exits cleanly"; printf '%s\n' "$OUT" | tail -8; fi

if grep -q 'Smoke Title' "$work/dist/hello.html"; then
  ok "emitted html contains title"
else
  bad "emitted html contains title"
fi

if grep -q 'Smoke body text' "$work/dist/hello.html"; then
  ok "emitted html contains body"
else
  bad "emitted html contains body"
fi

rm -rf "$work"
trap - EXIT

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]