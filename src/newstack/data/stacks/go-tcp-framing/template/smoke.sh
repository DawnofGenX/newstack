#!/usr/bin/env bash
# Talk to the service the way its users must: raw TCP, length-prefixed frames.
set -euo pipefail

cd "$(dirname "$0")"
PORT=${PORT:-5481}
HOST=${HOST:-127.0.0.1}
PY=${PY:-python3}

mkdir -p build
go build -o build/blog-frame .

if "$PY" - "$HOST" "$PORT" 2>/dev/null <<'PY'
import socket
import sys

sock = socket.create_connection((sys.argv[1], int(sys.argv[2])), timeout=1)
sock.close()
PY
then
    echo "port $PORT is already answering - stop that process before running this step" >&2
    exit 1
fi

./build/blog-frame &
server=$!
trap 'kill -TERM "$server" 2>/dev/null || true; for _ in $(seq 1 20); do kill -0 "$server" 2>/dev/null || break; sleep 0.1; done; kill -KILL "$server" 2>/dev/null || true; wait "$server" 2>/dev/null || true' EXIT

for _ in $(seq 1 160); do
    if "$PY" - "$HOST" "$PORT" <<'PY' 2>/dev/null
import socket
import sys

sock = socket.create_connection((sys.argv[1], int(sys.argv[2])), timeout=1)
sock.close()
PY
    then
        break
    fi
    sleep 0.25
done
kill -0 "$server"

# The client below is deliberately written against the wire format, not against
# a shared library: a framing bug that both sides share would otherwise pass.
"$PY" - "$HOST" "$PORT" <<'PY'
import json
import socket
import struct
import sys

host, port = sys.argv[1], int(sys.argv[2])
checks = 0


def fail(name, detail):
    print(f"FAIL {name}: {detail}", file=sys.stderr)
    raise SystemExit(1)


def ok(name):
    global checks
    checks += 1
    print(f"ok {name}")


class Client:
    def __init__(self):
        self.sock = socket.create_connection((host, port), timeout=10)
        self.buffer = b""

    def send(self, payload):
        if isinstance(payload, str):
            payload = payload.encode()
        self.sock.sendall(struct.pack(">I", len(payload)) + payload)
        return self.receive()

    def receive(self):
        while len(self.buffer) < 4:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise RuntimeError("the server closed the connection")
            self.buffer += chunk
        (size,) = struct.unpack(">I", self.buffer[:4])
        while len(self.buffer) < 4 + size:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise RuntimeError("the frame was truncated")
            self.buffer += chunk
        payload, self.buffer = self.buffer[4:4 + size], self.buffer[4 + size:]
        return json.loads(payload)

    def close(self):
        self.sock.close()


client = Client()

reply = client.send('{"op":"ping"}')
if not (reply["ok"] and reply.get("pong") is True):
    fail("ping", reply)
ok("ping")

reply = client.send('{"op":"count","text":"a b\\nc\\n"}')
if (reply["lines"], reply["words"], reply["bytes"]) != (2, 3, 6):
    fail("count", reply)
ok("count")

reply = client.send(json.dumps({"op": "count", "text": "h\u00e9llo w\u00f6rld\n"}))
if (reply["lines"], reply["words"], reply["bytes"]) != (1, 2, 14):
    fail("utf8 counts bytes", reply)
ok("utf8 counts 14 bytes, not 12 characters")

reply = client.send('{"op":"count","text":""}')
if (reply["lines"], reply["words"], reply["bytes"]) != (0, 0, 0):
    fail("empty text must report zeros, not omit them", reply)
ok("zero counts are printed")

reply = client.send('{"op":"count"}')
if reply["error"] != "missing_text":
    fail("missing text", reply)
ok("missing_text")

reply = client.send('{"op":"mystery"}')
if reply["error"] != "unknown_op":
    fail("unknown op", reply)
ok("unknown_op")

reply = client.send('{"text":"a b"}')
if reply["error"] != "missing_op":
    fail("missing op", reply)
ok("missing_op")

reply = client.send("this is not json")
if reply["error"] != "invalid_json":
    fail("broken json", reply)
ok("invalid_json")

reply = client.send('{"op":"ping"}')
if not reply["ok"]:
    fail("the connection must survive protocol errors", reply)
ok("the connection survives protocol errors")

big = "x " * 4000
reply = client.send(json.dumps({"op": "count", "text": big}))
if (reply["words"], reply["bytes"]) != (4000, 8000):
    fail("an 8 KB frame", reply)
ok("an 8 KB frame is ordinary traffic")

for step in range(1, 51):
    reply = client.send(json.dumps({"op": "count", "text": "a" * step}))
    if reply["bytes"] != step:
        fail(f"request {step} came back out of order", reply)
ok("50 requests came back in order on one connection")

client.close()

# A frame header promising more than the cap must be refused before the body
# is read -- the length prefix is an allocation instruction from the network.
rogue = socket.create_connection((host, port), timeout=10)
rogue.sendall(struct.pack(">I", 65537))
raw = rogue.recv(65536)
(size,) = struct.unpack(">I", raw[:4])
reply = json.loads(raw[4:4 + size])
if reply.get("error") != "frame_too_large":
    fail("oversized frame", reply)
ok("an oversized frame is refused")
rogue.close()

# The listener is still healthy after that client went away mid-frame.
second = Client()
if not second.send('{"op":"ping"}')["ok"]:
    fail("the listener stopped serving after a rogue client", "")
second.close()
ok("the listener still serves new connections")

print(f"smoke: all {checks} checks passed")
PY

echo "smoke: all checks passed"
