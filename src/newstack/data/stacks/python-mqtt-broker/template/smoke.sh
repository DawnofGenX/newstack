#!/usr/bin/env bash
# Drive the broker with the real mosquitto command-line clients.
set -euo pipefail

PORT="${PORT:-5488}"
HOST="${HOST:-127.0.0.1}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG="$ROOT/.mqtt.log"
PY="${PY:-$ROOT/.venv/bin/python}"

pass=0
fail=0

ok() {
  pass=$((pass + 1))
  echo "ok $pass - $1"
}

bad() {
  fail=$((fail + 1))
  echo "FAIL - $1${2:+: $2}"
}

listening() {
  "$PY" - "$HOST" "$PORT" <<'PY'
import socket, sys
host, port = sys.argv[1], int(sys.argv[2])
try:
    with socket.create_connection((host, port), timeout=0.5):
        pass
except OSError:
    raise SystemExit(1)
PY
}

if ! command -v mosquitto_pub >/dev/null || ! command -v mosquitto_sub >/dev/null; then
  echo "smoke: mosquitto clients are missing (apt-get install -y --no-install-recommends mosquitto-clients)" >&2
  exit 1
fi
if listening; then
  echo "smoke: port $PORT is already answering - stop that process before running this step" >&2
  exit 1
fi

work="$(mktemp -d)"
cd "$ROOT"
"$PY" -m {{ package_name }} --port "$PORT" >"$LOG" 2>&1 &
server=$!
trap 'kill -TERM "$server" 2>/dev/null || true; for _ in $(seq 1 20); do kill -0 "$server" 2>/dev/null || break; sleep 0.1; done; kill -KILL "$server" 2>/dev/null || true; wait "$server" 2>/dev/null || true; rm -rf "$work"' EXIT

ready=0
for _ in $(seq 1 160); do
  if listening; then ready=1; break; fi
  sleep 0.25
done
if [ "$ready" -ne 1 ] || ! kill -0 "$server" 2>/dev/null; then
  echo "smoke: the broker never started listening" >&2
  sed -n '1,20p' "$LOG" >&2
  exit 1
fi
ok "the broker listens on $PORT"

sub() { timeout 8 mosquitto_sub -h "$HOST" -p "$PORT" "$@"; }
pub() { mosquitto_pub -h "$HOST" -p "$PORT" "$@"; }

# -- one message at QoS 0 ---------------------------------------------
sub -t 'room/1' -C 1 -W 4 >"$work/q0.txt" &
watcher=$!
sleep 0.4
pub -t 'room/1' -m 'hello'
wait "$watcher" || true
if [ "$(cat "$work/q0.txt")" = "hello" ]; then ok "a QoS 0 message arrives"; else bad "a QoS 0 message arrives" "$(cat "$work/q0.txt")"; fi

# -- QoS 1 -------------------------------------------------------------
sub -t 'room/1' -q 1 -C 1 -W 4 >"$work/q1.txt" &
watcher=$!
sleep 0.4
pub -t 'room/1' -q 1 -m 'at-least-once'
wait "$watcher" || true
if [ "$(cat "$work/q1.txt")" = "at-least-once" ]; then ok "a QoS 1 message arrives"; else bad "a QoS 1 message arrives" "$(cat "$work/q1.txt")"; fi

# -- a wildcard filter -------------------------------------------------
sub -t 'room/#' -C 1 -W 4 >"$work/wild.txt" &
watcher=$!
sleep 0.4
pub -t 'room/2/deep' -m 'under-the-hash'
wait "$watcher" || true
if [ "$(cat "$work/wild.txt")" = "under-the-hash" ]; then ok "a room/# filter sees a deep topic"; else bad "a room/# filter sees a deep topic" "$(cat "$work/wild.txt")"; fi

# -- two subscribers ---------------------------------------------------
sub -t 'both/1' -C 1 -W 4 >"$work/first.txt" &
one=$!
sub -t 'both/1' -C 1 -W 4 >"$work/second.txt" &
two=$!
sleep 0.5
pub -t 'both/1' -m 'shared'
wait "$one" || true
wait "$two" || true
if [ "$(cat "$work/first.txt")" = "shared" ] && [ "$(cat "$work/second.txt")" = "shared" ]; then
  ok "both subscribers get a copy"
else
  bad "both subscribers get a copy" "$(cat "$work/first.txt") / $(cat "$work/second.txt")"
fi

# -- retained messages --------------------------------------------------
pub -t 'slow/1' -q 1 -r -m 'kept'
sub -t 'slow/#' -C 1 -W 4 -F '%t|%p|%r' >"$work/retained.txt"
if [ "$(cat "$work/retained.txt")" = "slow/1|kept|1" ]; then
  ok "a retained message reaches a later subscriber"
else
  bad "a retained message reaches a later subscriber" "$(cat "$work/retained.txt")"
fi

pub -t 'slow/1' -q 1 -r -n
if sub -t 'slow/#' -C 1 -W 1 >"$work/gone.txt" 2>/dev/null; then
  bad "an empty retained publish deletes the record" "$(cat "$work/gone.txt")"
else
  ok "an empty retained publish deletes the record"
fi

# -- a large payload ----------------------------------------------------
# mosquitto_sub terminates whatever it prints with a newline, so compare the
# first 20000 bytes and assert the extra byte is that newline.
# Build the payload without a truncating `head` at the end of the pipe:
# under `set -o pipefail` that head exits early, `tr` takes SIGPIPE and the
# whole pipeline fails about one run in three. 15000 bytes is 20000 base64
# characters, so a plain redirect is enough.
head -c 15000 /dev/urandom | base64 | tr -d '\n' >"$work/big.txt"
sub -t 'big/1' -C 1 -W 6 >"$work/big.out" &
watcher=$!
sleep 0.4
pub -t 'big/1' -q 1 -f "$work/big.txt"
wait "$watcher" || true
size="$(wc -c <"$work/big.out")"
head -c 20000 "$work/big.out" >"$work/big.first"
if cmp -s "$work/big.first" "$work/big.txt" && [ "$size" -eq 20001 ]; then
  ok "a 20 KB payload survives the wire"
else
  bad "a 20 KB payload survives the wire" "$size bytes received"
fi

# -- the broker's own refusals -----------------------------------------
if sub -t 'a/#/b' -C 1 -W 2 >"$work/badfilter.txt" 2>"$work/badfilter.err"; then
  bad "an invalid filter is refused" "the client reported success"
else
  ok "an invalid filter is refused"
fi

if pub -t 'a/+/c' -q 1 -m 'nope' >"$work/wildpub.out" 2>"$work/wildpub.err"; then
  bad "a wildcard publish closes the connection" "the client reported success"
else
  ok "a wildcard publish closes the connection"
fi

"$PY" - "$HOST" "$PORT" <<'PY' >"$work/ping.txt"
import sys
from {{ package_name }}.client import Client

client = Client(sys.argv[1], int(sys.argv[2]), "smoke-ping")
client.connect()
client.ping()
client.disconnect()
print("pong")
PY
if [ "$(cat "$work/ping.txt")" = "pong" ]; then ok "PINGREQ is answered"; else bad "PINGREQ is answered"; fi

echo "smoke: $pass checks, $fail failed"
if [ "$fail" -ne 0 ]; then
  sed -n '1,20p' "$LOG" >&2
  exit 1
fi
