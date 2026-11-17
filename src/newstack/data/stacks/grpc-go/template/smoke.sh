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
if ! command -v buf >/dev/null 2>&1 && ! command -v "$HOME/go/bin/buf" >/dev/null 2>&1; then
  echo "smoke: buf is missing (install buf)"
  exit 1
fi

echo "smoke: grpc-go"

export PATH="$(go env GOPATH)/bin:$PATH"

run sh -c 'go mod download && buf lint && buf generate'
if [ "$STATUS" -eq 0 ]; then ok "buf generate"; else bad "buf generate"; printf '%s\n' "$OUT" | tail -8; fi

run sh -c 'unformatted=$(gofmt -l cmd internal); if [ -n "$unformatted" ]; then echo "$unformatted"; exit 1; fi'
if [ "$STATUS" -eq 0 ]; then ok "gofmt clean"; else bad "gofmt clean"; printf '%s\n' "$OUT" | tail -8; fi

run go vet ./...
if [ "$STATUS" -eq 0 ]; then ok "go vet passes"; else bad "go vet passes"; printf '%s\n' "$OUT" | tail -8; fi

run go test ./...
if [ "$STATUS" -eq 0 ]; then ok "go test passes"; else bad "go test passes"; printf '%s\n' "$OUT" | tail -8; fi

run go build -o bin/probe ./cmd/probe
if [ "$STATUS" -eq 0 ]; then ok "build probe"; else bad "build probe"; printf '%s\n' "$OUT" | tail -8; fi

run go build -o bin/server ./cmd/{{ npm_name }}
if [ "$STATUS" -eq 0 ]; then ok "build server"; else bad "build server"; printf '%s\n' "$OUT" | tail -8; fi

PORT=50071
BASE="127.0.0.1:${PORT}"
work=$(mktemp -d)
srv=""
trap 'if [ -n "$srv" ]; then kill "$srv" 2>/dev/null || true; wait "$srv" 2>/dev/null || true; fi; rm -rf "$work"' EXIT

if [ -x ./bin/server ] && [ -x ./bin/probe ]; then
  PORT="$PORT" ./bin/server >"$work/server.log" 2>&1 &
  srv=$!
  ready=0
  i=0
  while [ "$i" -lt 60 ]; do
    if ./bin/probe -addr "$BASE" >/dev/null 2>&1; then ready=0; break; fi
    i=$((i + 1))
    sleep 0.5
  done
  # probe returns 0 on success; track via status file
  if ./bin/probe -addr "$BASE" >"$work/probe1.out" 2>&1; then
    ok "probe succeeds"
  else
    bad "probe succeeds"
    cat "$work/probe1.out" >&2 || true
  fi
  if grep -q 'lines=1 words=2 bytes=12' "$work/probe1.out" 2>/dev/null; then ok "probe first output"; else bad "probe first output"; fi

  if ./bin/probe -addr "$BASE" -text 'a b
c
' >"$work/probe2.out" 2>&1; then
    ok "probe second succeeds"
  else
    bad "probe second succeeds"
  fi
  if grep -q 'lines=2 words=3 bytes=6' "$work/probe2.out" 2>/dev/null; then ok "probe second output"; else bad "probe second output"; fi

  kill "$srv" 2>/dev/null || true
  wait "$srv" 2>/dev/null || true
  srv=""
  trap - EXIT
  rm -rf "$work"
else
  bad "built binaries exist"
fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]