#!/usr/bin/env bash
# Run the suite, then prove it left nothing behind on the fixture port.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
PORT=${PORT:-5466}
cd "$ROOT"

if curl -fsS --max-time 2 "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1; then
  echo "port ${PORT} is already answering - stop that process before running this step" >&2
  exit 1
fi

npx playwright test --reporter=line

if ss -ltn 2>/dev/null | grep -q ":${PORT}\b"; then
  echo "the fixture server is still listening on ${PORT} after the run" >&2
  exit 1
fi
echo "smoke: suite passed and port ${PORT} is free"
