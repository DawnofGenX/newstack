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
if [ -x "$binary" ]; then echo "ok   release binary exists"; else echo "FAIL release binary exists"; fail=1; fi

if [ "$fail" -eq 0 ]; then
  cat >"$work/config.json" <<'JSON'
{"host":"filehost","port":9090,"debug":false,"name":"fileapp"}
JSON

  set +e
  APP_PORT=7070 APP_DEBUG=true "$binary" print --config "$work/config.json" >"$work/out.json" 2>"$work/err.log"
  status=$?
  set -e
  if [ "$status" -eq 0 ]; then echo "ok   print exits zero"; else echo "FAIL print exits zero ($status)"; fail=1; cat "$work/err.log"; fi

  if grep -q '"port": 7070' "$work/out.json" && grep -q '"debug": true' "$work/out.json" && grep -q '"host": "filehost"' "$work/out.json"; then
    echo "ok   env overrides winning values"
  else
    echo "FAIL env overrides winning values"; fail=1; cat "$work/out.json"
  fi

  set +e
  APP_PORT=7070 "$binary" explain --config "$work/config.json" >"$work/explain.txt" 2>"$work/err2.log"
  status=$?
  set -e
  if [ "$status" -eq 0 ]; then echo "ok   explain exits zero"; else echo "FAIL explain exits zero ($status)"; fail=1; cat "$work/err2.log"; fi

  if grep -q 'port = 7070 (env)' "$work/explain.txt" && grep -q 'host = filehost (file)' "$work/explain.txt"; then
    echo "ok   explain shows winning layers"
  else
    echo "FAIL explain shows winning layers"; fail=1; cat "$work/explain.txt"
  fi
fi

[ "$fail" -eq 0 ] || { echo "smoke: FAILED"; exit 1; }
echo "smoke: all checks passed"