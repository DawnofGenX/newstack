#!/usr/bin/env bash
# End-to-end smoke test for {{ package_name }} on port 5489. Green = exit 0.
set -euo pipefail
cd "$(dirname "$0")"

PY=".venv/bin/python"
PORT=5489
SERVER_PID=""
CHECKS=0
FAILED=0
OUT="$(mktemp -d)"
trap 'rm -rf "$OUT"' EXIT

note() { echo "ok  $*"; CHECKS=$((CHECKS + 1)); }
fail() { echo "FAIL $*"; CHECKS=$((CHECKS + 1)); FAILED=$((FAILED + 1)); }

cleanup() {
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill -TERM "$SERVER_PID" 2>/dev/null || true
    for _ in $(seq 20); do
      kill -0 "$SERVER_PID" 2>/dev/null || break
      sleep 0.1
    done
    kill -KILL "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

# --- pre-flight: port must be ours -------------------------------------------
if (exec 3<>"/dev/tcp/127.0.0.1/${PORT}") 2>/dev/null; then
  echo "port 5489 is already answering - stop that process before running this step" >&2
  exit 1
fi
note "port ${PORT} free before start"

# --- start server + readiness poll (160 x 0.25s = 40s) ------------------------
"$PY" -m {{ package_name }} --host 127.0.0.1 --port "$PORT" >"$OUT/server.log" 2>&1 &
SERVER_PID=$!
ready=0
for _ in $(seq 160); do
  if (exec 3<>"/dev/tcp/127.0.0.1/${PORT}") 2>/dev/null; then ready=1; break; fi
  sleep 0.25
done
if [[ "$ready" != 1 ]]; then
  echo "server never became ready on ${PORT}" >&2
  cat "$OUT/server.log" >&2 || true
  exit 1
fi
note "server up (pid ${SERVER_PID})"

# --- 1. handshake rejection over plain HTTP (curl) ----------------------------
code="$(curl -s --max-time 5 -o /dev/null -w '%{http_code}' "http://127.0.0.1:${PORT}/nope" || echo err)"
[[ "$code" == "404" ]] && note "curl rejection bad-path -> 404" || fail "bad-path got $code"
code="$(curl -s --max-time 5 -o "$OUT/h.txt" -D "$OUT/h.head" -w '%{http_code}' \
  -H 'Upgrade: websocket' -H 'Connection: Upgrade' \
  -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' -H 'Sec-WebSocket-Version: 8' \
  "http://127.0.0.1:${PORT}/ws" || echo err)"
[[ "$code" == "426" ]] && grep -q "Sec-WebSocket-Version: 13" "$OUT/h.head" \
  && note "curl version rejection -> 426 + Version: 13" || fail "version-reject got $code"

# --- 2-5. real-socket client checks (python, masking client) ------------------
CLIENT_RC=0
"$PY" - "$PORT" >"$OUT/client.log" 2>&1 <<'PYEOF' || CLIENT_RC=$?
import json, sys
from {{ package_name }}.client import WSClient
port = int(sys.argv[1])
def ok(name, cond):
    print(("ok  " if cond else "FAIL ") + name)
    if not cond:
        sys.exit(1)

c = WSClient("127.0.0.1", port)
c.send_text(json.dumps({"type": "stats", "text": "hello world\n"}))
ok("stats roundtrip", json.loads(c.recv_text(5)) ==
   {"type": "stats", "lines": 1, "words": 2, "bytes": 12})
c.send_text(json.dumps({"type": "echo", "text": "smoke"}))
ok("echo roundtrip", json.loads(c.recv_text(5)) == {"type": "echo", "text": "smoke"})
c.send_text(json.dumps({"type": "ping"}))
ok("ping roundtrip", json.loads(c.recv_text(5)) == {"type": "pong"})

# fragmentation: 3 frames, one reply
def masked(fin, op, payload):
    key = b"\x0a\x0b\x0c\x0d"
    m = bytes(b ^ key[i % 4] for i, b in enumerate(payload))
    return bytes([(0x80 if fin else 0) | op, 0x80 | len(payload)]) + key + m
c.sock.sendall(masked(False, 0x1, b'{"type":"ech'))
c.sock.sendall(masked(False, 0x0, b'o","text":"f"}'))
c.sock.sendall(masked(True, 0x0, b""))
ok("fragmented reassembly", json.loads(c.recv_text(5)) == {"type": "echo", "text": "f"})
c.close()

# unmasked frame -> close 1002, then socket dies
c = WSClient("127.0.0.1", port)
from {{ package_name }}.frames import encode
c.sock.sendall(encode(0x1, b"{}", mask=False))
f = c.receive(5)
ok("unmasked -> close 1002", f.opcode == 0x8 and int.from_bytes(f.payload[:2], "big") == 1002)
c.close()

# clean close: server echoes our code and shuts the TCP connection
c = WSClient("127.0.0.1", port)
c.send_close(1000)
f = c.receive(5)
echoed = f.opcode == 0x8 and int.from_bytes(f.payload[:2], "big") == 1000
try:
    eof = c.sock.recv(1) == b""
except (EOFError, OSError):
    eof = True
ok("clean close echo 1000 + TCP closed", echoed and eof)
c.close()
PYEOF
if [[ "$CLIENT_RC" != 0 ]]; then
  cat "$OUT/client.log" >&2 || true
  echo "FAIL client socket checks (see above)"; CHECKS=$((CHECKS + 1)); FAILED=$((FAILED + 1))
else
  while IFS= read -r line; do
    case "$line" in ok\ *) note "client: ${line#ok  }";; *) fail "client: ${line#FAIL }";; esac
  done < <(cat "$OUT/client.log")
fi

# --- port released after server exit ------------------------------------------
kill -TERM "$SERVER_PID" 2>/dev/null || true
for _ in $(seq 20); do kill -0 "$SERVER_PID" 2>/dev/null || break; sleep 0.1; done
wait "$SERVER_PID" 2>/dev/null || true
SERVER_PID=""
if (exec 3<>"/dev/tcp/127.0.0.1/${PORT}") 2>/dev/null; then
  fail "port ${PORT} still answering after shutdown"
else
  note "port ${PORT} released after shutdown"
fi

echo "smoke: ${CHECKS} checks, ${FAILED} failed"
[[ "$FAILED" == 0 ]] || exit 1
