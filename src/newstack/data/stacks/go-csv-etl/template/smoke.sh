#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

run() { set +e; OUT=$("$@" 2>&1); STATUS=$?; set -e; }

echo "smoke: go-csv-etl"

run go vet ./...
if [ "$STATUS" -eq 0 ]; then ok "go vet passes"; else bad "go vet passes"; printf '%s\n' "$OUT" | tail -8; fi

run go test ./...
if [ "$STATUS" -eq 0 ]; then ok "go test passes"; else bad "go test passes"; printf '%s\n' "$OUT" | tail -8; fi

run go build -o bin/etl .
if [ "$STATUS" -eq 0 ]; then ok "go build"; else bad "go build"; printf '%s\n' "$OUT" | tail -8; fi

if [ -x ./bin/etl ]; then
  out=$(./bin/etl -in data/input.csv)
  if printf '%s' "$out" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['count']==3 and d['total']==35.75 and d['unique_emails']==3, d"; then
    ok "CLI totals correct"
  else
    bad "CLI totals correct"
    printf '       got: %s\n' "$out"
  fi
else
  bad "binary exists"
fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
