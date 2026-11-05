#!/usr/bin/env bash
# Talk RESP to the render: redis-cli for the ordinary commands, raw sockets for
# the framing cases redis-cli cannot express.
set -euo pipefail

PORT="${PORT:-5486}"
HOST="127.0.0.1"
LOG=".resp.log"
failures=0

check() { # check <name> <expected> <actual>
  if [ "$2" = "$3" ]; then
    echo "ok $1"
  else
    echo "FAIL $1: want [$2] got [$3]"
    failures=$((failures + 1))
  fi
}

contains() { # contains <name> <needle> <haystack>
  case "$3" in
    *"$2"*) echo "ok $1" ;;
    *)
      echo "FAIL $1: [$2] not in [$3]"
      failures=$((failures + 1))
      ;;
  esac
}

listening() {
  python3 - "$HOST" "$PORT" <<'PY'
import socket, sys
try:
    with socket.create_connection((sys.argv[1], int(sys.argv[2])), timeout=0.3):
        pass
except OSError:
    sys.exit(1)
PY
}

if listening; then
  echo "port $PORT is already answering - stop that process before running this step" >&2
  exit 1
fi

if ! command -v redis-cli > /dev/null; then
  echo "redis-cli is missing: apt-get install -y --no-install-recommends redis-tools" >&2
  exit 1
fi

rm -f "$LOG"
PORT="$PORT" .venv/bin/python -m {{ package_name }} --port "$PORT" > "$LOG" 2>&1 &
server=$!
# The trap must wait for the process: signalling alone leaves the port in
# use for the next run.
trap 'kill -TERM "$server" 2>/dev/null || true; for _ in $(seq 1 20); do kill -0 "$server" 2>/dev/null || break; sleep 0.1; done; kill -KILL "$server" 2>/dev/null || true; wait "$server" 2>/dev/null || true' EXIT

ready=0
for _ in $(seq 1 160); do
  if listening; then ready=1; break; fi
  sleep 0.25
done
if [ "$ready" -ne 1 ]; then
  echo "the server never answered on $PORT" >&2
  tail -20 "$LOG" >&2
  exit 1
fi
kill -0 "$server"

redis() { redis-cli -h "$HOST" -p "$PORT" "$@"; }

check "ping" "PONG" "$(redis ping)"
check "set" "OK" "$(redis set greeting hello)"
check "get" "hello" "$(redis get greeting)"
check "get missing" "" "$(redis get nothing)"
check "ttl without expiry" "-1" "$(redis ttl greeting)"
check "set with ex 60" "OK" "$(redis set session token EX 60)"
check "ttl rounds up" "60" "$(redis ttl session)"
check "incr" "1" "$(redis incr counter)"
check "incr again" "2" "$(redis incr counter)"
check "decr" "1" "$(redis decr counter)"
check "type" "string" "$(redis type greeting)"
check "type missing" "none" "$(redis type nothing)"
check "exists" "1" "$(redis exists greeting)"
check "del" "1" "$(redis del greeting)"
check "del again" "0" "$(redis del greeting)"
check "keys glob" "counter" "$(redis keys 'cou*' | tr -d '"')"
check "dbsize" "2" "$(redis dbsize)"

contains "unknown command" "unknown command" "$(redis nosuchcommand 2>&1)"
contains "arity error" "wrong number of arguments" "$(redis get 2>&1)"
contains "syntax error" "syntax error" "$(redis set a b NX 2>&1)"
contains "bad expire" "invalid expire time" "$(redis set a b EX 0 2>&1)"
check "the connection survived those errors" "PONG" "$(redis ping)"

# Framing: raw bytes, no client library involved.
framing=$(
  python3 - "$HOST" "$PORT" <<'PY'
import socket, sys

host, port = sys.argv[1], int(sys.argv[2])
blob = b"\x00\xffbytes"
command = b"*2\r\n$4\r\nECHO\r\n$%d\r\n%s\r\n" % (len(blob), blob)
with socket.create_connection((host, port), timeout=5) as sock:
    sock.sendall(command)
    reply = b""
    while len(reply) < len(blob) + 6:
        chunk = sock.recv(64)
        if not chunk:
            break
        reply += chunk
    header, _, rest = reply.partition(b"\r\n")
    print(header.decode("ascii"), "same-bytes" if rest[: len(blob)] == blob else "different-bytes")
PY
)
check "binary echo is framed as a bulk and keeps its bytes" "\$7 same-bytes" "$framing"

# Two commands in one write must produce two replies, in order.
pipeline=$(
  python3 - "$HOST" "$PORT" <<'PY'
import socket, sys

host, port = sys.argv[1], int(sys.argv[2])
payload = b"*1\r\n$4\r\nPING\r\n*2\r\n$4\r\nECHO\r\n$2\r\nhi\r\n"


def read_line(sock):
    line = b""
    while not line.endswith(b"\r\n"):
        line += sock.recv(1)
    return line[:-2]


with socket.create_connection((host, port), timeout=5) as sock:
    sock.sendall(payload)
    first = read_line(sock)[1:].decode()
    size = int(read_line(sock)[1:])
    second = sock.recv(size + 2)[:-2].decode()
    print(first, second, sep="/")
PY
)
check "pipelined replies keep their order" "PONG/hi" "$pipeline"

# A malformed frame is one error line and then a close.
broken=$(
  python3 - "$HOST" "$PORT" <<'PY'
import socket, sys
host, port = sys.argv[1], int(sys.argv[2])
with socket.create_connection((host, port), timeout=5) as sock:
    sock.sendall(b"*1\r\n$abc\r\nPING\r\n")
    first = sock.recv(256)
    second = sock.recv(256)
    print("error" if b"Protocol error" in first else "no-error", "closed" if second == b"" else "open")
PY
)
check "a malformed frame is an error then a close" "error closed" "$broken"

check "flushdb" "OK" "$(redis flushdb)"
check "dbsize after flush" "0" "$(redis dbsize)"
kill -0 "$server"
check "the server is still running" "yes" "yes"

if [ "$failures" -ne 0 ]; then
  echo "smoke: $failures check(s) failed"
  exit 1
fi
echo "smoke: all checks passed"
