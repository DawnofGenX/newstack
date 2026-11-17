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

if ! command -v docker >/dev/null 2>&1; then
  echo "smoke: docker is missing (install docker)"
  exit 1
fi

echo "smoke: docker-compose-svc"

# Validate the compose file without starting containers.
run docker compose config -q
if [ "$STATUS" -eq 0 ]; then ok "compose config valid"; else bad "compose config valid"; printf '%s\n' "$OUT" | tail -8; fi

# Ensure the declared services exist.
services=$(docker compose config --services 2>/dev/null || true)
if printf '%s\n' "$services" | grep -qx 'web'; then ok "service web declared"; else bad "service web declared"; fi

# If the daemon is unavailable, skip the runtime part with a clear message.
if docker info >/dev/null 2>&1; then
  ok "docker daemon available"
  # optional: build image
  run docker compose build
  if [ "$STATUS" -eq 0 ]; then ok "compose build"; else bad "compose build"; printf '%s\n' "$OUT" | tail -8; fi
else
  echo "smoke: docker daemon unavailable - skipping runtime checks"
fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]