#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

if ! command -v go >/dev/null 2>&1; then echo "smoke: go missing"; exit 1; fi
if ! command -v curl >/dev/null 2>&1; then echo "smoke: curl missing"; exit 1; fi
if ! command -v python3 >/dev/null 2>&1; then echo "smoke: python3 missing"; exit 1; fi

echo "smoke: go-http-proxy"

run() { set +e; OUT=$("$@" 2>&1); STATUS=$?; set -e; }

run go vet ./...
if [ "$STATUS" -eq 0 ]; then ok "go vet passes"; else bad "go vet passes"; printf '%s\n' "$OUT" | tail -8; fi

run go test ./...
if [ "$STATUS" -eq 0 ]; then ok "go test passes"; else bad "go test passes"; printf '%s\n' "$OUT" | tail -8; fi

run go build -o bin/server .
if [ "$STATUS" -eq 0 ]; then ok "go build"; else bad "go build"; printf '%s\n' "$OUT" | tail -8; fi

work=$(mktemp -d)
up=""
srv=""
trap 'if [ -n "$srv" ]; then kill "$srv" 2>/dev/null || true; wait "$srv" 2>/dev/null || true; fi; if [ -n "$up" ]; then kill "$up" 2>/dev/null || true; wait "$up" 2>/dev/null || true; fi; rm -rf "$work"' EXIT

cat > "$work/upstream.py" <<'PY'
import http.server, socketserver
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        xff = self.headers.get("X-Forwarded-For", "")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("X-Seen-XFF", xff)
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        self.wfile.write(b"upstream-ok")
    def log_message(self, *a):
        pass
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", 5542), H) as httpd:
    httpd.serve_forever()
PY

python3 "$work/upstream.py" >"$work/upstream.log" 2>&1 &
up=$!

# wait for upstream
ready=0
i=0
while [ "$i" -lt 60 ]; do
  code=$(curl --max-time 2 -sS -o /dev/null -w '%{http_code}' http://127.0.0.1:5542/ 2>/dev/null || true)
  if [ "$code" = "200" ]; then ready=1; break; fi
  i=$((i + 1))
  sleep 0.5
done
if [ "$ready" -ne 1 ]; then
  bad "upstream becomes ready"
  cat "$work/upstream.log" >&2 || true
  exit 1
fi
ok "upstream becomes ready"

if [ -x ./bin/server ]; then
  UPSTREAM=http://127.0.0.1:5542 PORT=5541 ./bin/server >"$work/server.log" 2>&1 &
  srv=$!
  ready=0
  i=0
  while [ "$i" -lt 60 ]; do
    code=$(curl --max-time 2 -sS -o /dev/null -w '%{http_code}' http://127.0.0.1:5541/health 2>/dev/null || true)
    if [ "$code" = "200" ]; then ready=1; break; fi
    i=$((i + 1))
    sleep 0.5
  done
  if [ "$ready" -eq 1 ]; then
    ok "proxy becomes ready"
    headers=$(mktemp)
    body=$(curl --max-time 10 -sS -D "$headers" -o - http://127.0.0.1:5541/foo 2>/dev/null || true)
    if [ "$body" = "upstream-ok" ]; then ok "proxy forwards body"; else bad "proxy forwards body"; printf '       got: %s\n' "$body"; fi
    if grep -qi 'X-Seen-XFF: ' "$headers"; then
      xff=$(grep -i 'X-Seen-XFF:' "$headers" | head -1)
      if printf '%s' "$xff" | grep -q '127.0.0.1'; then ok "X-Forwarded-For injected"; else bad "X-Forwarded-For injected"; fi
    else
      bad "X-Seen-XFF header present"
    fi
    if grep -qi '^Connection:' "$headers"; then bad "hop-by-hop Connection stripped"; else ok "hop-by-hop Connection stripped"; fi
  else
    bad "proxy becomes ready"
    cat "$work/server.log" >&2 || true
  fi
  kill "$srv" 2>/dev/null || true
  wait "$srv" 2>/dev/null || true
  srv=""
else
  bad "server binary exists"
fi

kill "$up" 2>/dev/null || true
wait "$up" 2>/dev/null || true
up=""

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
