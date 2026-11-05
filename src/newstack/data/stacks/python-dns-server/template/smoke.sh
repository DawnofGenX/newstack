#!/usr/bin/env bash
# Exercise the running server with dig: every answer the zone promises, plus
# the four statuses a resolver can legitimately get back.
set -euo pipefail

PORT="${PORT:-5487}"
HOST=127.0.0.1
LOG=".dns.log"
export PORT

command -v dig > /dev/null || {
  echo "smoke: dig is required - apt-get install -y --no-install-recommends dnsutils" >&2
  exit 1
}

listening() {
  python3 - "$HOST" "$PORT" <<'PY' 2>/dev/null
import socket, sys
host, port = sys.argv[1], int(sys.argv[2])
for kind in (socket.SOCK_DGRAM, socket.SOCK_STREAM):
    probe = socket.socket(socket.AF_INET, kind)
    probe.settimeout(0.5)
    try:
        probe.connect((host, port))
    except OSError:
        raise SystemExit(1)
    finally:
        probe.close()
PY
}

if listening; then
  echo "smoke: port $PORT is already answering - stop that process before running this step" >&2
  exit 1
fi

checks=0
failures=0
check() {
  local name=$1 want=$2 got=$3
  checks=$((checks + 1))
  if [ "$got" = "$want" ]; then
    echo "ok $checks - $name"
  else
    failures=$((failures + 1))
    echo "FAIL $checks - $name: want '$want', got '$got'"
  fi
}

contains() {
  local name=$1 want=$2 haystack=$3
  checks=$((checks + 1))
  case "$haystack" in
    *"$want"*) echo "ok $checks - $name" ;;
    *)
      failures=$((failures + 1))
      echo "FAIL $checks - $name: '$want' not in '$haystack'"
      ;;
  esac
}

.venv/bin/python -m {{ package_name }} --port "$PORT" 2> "$LOG" &
server=$!
trap 'kill -TERM "$server" 2>/dev/null || true
      for _ in $(seq 1 20); do kill -0 "$server" 2>/dev/null || break; sleep 0.1; done
      kill -KILL "$server" 2>/dev/null || true
      wait "$server" 2>/dev/null || true' EXIT

ready=no
for _ in $(seq 1 160); do
  if listening; then ready=yes; break; fi
  sleep 0.25
done
if [ "$ready" != yes ]; then
  echo "smoke: the server never started listening; log follows" >&2
  cat "$LOG" >&2
  exit 1
fi
kill -0 "$server"

# +ignore keeps dig from quietly retrying over TCP after a truncated answer.
d() { dig +ignore +short "@$HOST" -p "$PORT" "$@"; }
status() { dig +ignore "@$HOST" -p "$PORT" +noall +comments "$@" | grep -o 'status: [A-Z]*' | head -1; }

check "A records" "192.0.2.11
192.0.2.12" "$(d www.example.test A | sort)"
check "the apex A record" "192.0.2.10" "$(d example.test A)"
check "AAAA" "2001:db8::10" "$(d example.test AAAA)"
check "TXT" '"v=spf1 -all"' "$(d example.test TXT)"
check "MX" "10 mail.example.test." "$(d example.test MX)"
check "NS" "ns1.example.test." "$(d example.test NS)"
contains "a CNAME is followed" "www.example.test." "$(d alias.example.test A)"
contains "two CNAME hops resolve" "192.0.2.12" "$(d chain.example.test A)"
check "names are case insensitive" "192.0.2.11
192.0.2.12" "$(d WWW.EXAMPLE.TEST A | sort)"

check "a known name is NOERROR" "status: NOERROR" "$(status www.example.test A)"
check "an unknown name is NXDOMAIN" "status: NXDOMAIN" "$(status nope.example.test A)"
check "a name outside the zone is REFUSED" "status: REFUSED" "$(status example.org A)"
check "an unknown class is NOTIMP" "status: NOTIMP" "$(status -c CH example.test A)"
check "the SOA is served" "status: NOERROR" "$(status example.test SOA)"
check "ANY returns the addresses" "192.0.2.11" "$(d www.example.test ANY | head -1)"

check "the big TXT does not fit plain UDP" "" "$(d +noedns big.example.test TXT)"
contains "and it comes back truncated" "tc" "$(dig +ignore "@$HOST" -p "$PORT" +noedns +noall +comments big.example.test TXT | grep -o 'flags:[^;]*')"
check "the big TXT is 510 bytes over TCP" "510" "$(d +tcp big.example.test TXT | tr -d '" \n' | wc -c | tr -d ' ')"
check "EDNS0 raises the limit" "510" "$(d +bufsize=4096 big.example.test TXT | tr -d '" \n' | wc -c | tr -d ' ')"
check "TCP answers the same as UDP" "192.0.2.11
192.0.2.12" "$(d +tcp www.example.test A | sort)"

echo "smoke: $checks checks, $failures failed"
[ "$failures" -eq 0 ]
