#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="$(mktemp -d)"
fail=0

cleanup() { rm -rf "$work"; }
trap cleanup EXIT

cd "$ROOT"

run() {
  set +e
  OUT=$("$@" 2>&1)
  STATUS=$?
  set -e
}

run cargo fmt --check
if [ "$STATUS" -eq 0 ]; then echo "ok   cargo fmt"; else echo "FAIL cargo fmt"; fail=1; printf '%s\n' "$OUT" | tail -8; fi

run cargo clippy --all-targets -- -D warnings
if [ "$STATUS" -eq 0 ]; then echo "ok   cargo clippy"; else echo "FAIL cargo clippy"; fail=1; printf '%s\n' "$OUT" | tail -8; fi

run cargo test
if [ "$STATUS" -eq 0 ]; then echo "ok   cargo test"; else echo "FAIL cargo test"; fail=1; printf '%s\n' "$OUT" | tail -8; fi

run cargo build --release
if [ "$STATUS" -eq 0 ]; then echo "ok   cargo build --release"; else echo "FAIL cargo build --release"; fail=1; printf '%s\n' "$OUT" | tail -8; fi

binary="./target/release/{{ npm_name }}"
if [ -x "$binary" ]; then
  echo "ok   release binary exists"
else
  echo "FAIL release binary exists"
  fail=1
fi

if [ "$fail" -eq 0 ]; then
  cat >"$work/requests.jsonl" <<'JSONL'
{"jsonrpc":"2.0","id":1,"method":"add","params":{"a":2,"b":3}}
{"jsonrpc":"2.0","method":"notes.put","params":{"title":"first","body":"no answer please"}}
{"jsonrpc":"2.0","id":2,"method":"notes.list"}
{"jsonrpc":"2.0","id":3,"method":"nope"}
not json at all
[]
JSONL

  set +e
  "$binary" <"$work/requests.jsonl" >"$work/responses.jsonl" 2>"$work/stderr.log"
  status=$?
  set -e

  if [ "$status" -eq 0 ]; then echo "ok   server exits zero"; else echo "FAIL server exits zero ($status)"; fail=1; fi

  # Six requests in, five answers out: the notification is executed silently.
  lines=$(wc -l <"$work/responses.jsonl" | tr -d ' ')
  if [ "$lines" = "5" ]; then echo "ok   one line per answered request (5)"; else echo "FAIL one line per answered request (got $lines)"; fail=1; fi

  expect() {
    if grep -Fq "$2" "$work/responses.jsonl"; then echo "ok   $1"; else echo "FAIL $1"; fail=1; fi
  }

  expect "add returns the sum" '"sum":5'
  expect "the notification mutated state" '"count":1'
  expect "unknown method is -32601" '"code":-32601'
  expect "a malformed line is -32700" '"code":-32700'
  expect "an empty batch is -32600" '"code":-32600'

  # Five answers for six requests is the whole notification contract: the sixth
  # line was executed (hence the count above) and never answered.
  envelopes=$(grep -Fc '"jsonrpc":"2.0"' "$work/responses.jsonl" | tr -d ' ')
  if [ "$envelopes" = "5" ]; then
    echo "ok   every answer is a JSON-RPC envelope"
  else
    echo "FAIL every answer is a JSON-RPC envelope (got $envelopes)"; fail=1
  fi

  if grep -Fq 'request(s) handled' "$work/stderr.log"; then
    echo "ok   the session summary goes to stderr"
  else
    echo "FAIL the session summary goes to stderr"; fail=1
  fi

  if [ -s "$work/stderr.log" ] && grep -Fq 'handled' "$work/responses.jsonl"; then
    echo "FAIL stderr leaked into the response stream"; fail=1
  else
    echo "ok   stderr stays off the response stream"
  fi
fi

[ "$fail" -eq 0 ] || { echo "smoke: FAILED"; exit 1; }
echo "smoke: all checks passed"
