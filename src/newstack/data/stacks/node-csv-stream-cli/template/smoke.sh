#!/bin/sh
set -eu

echo "smoke: node-csv-stream-cli"

run() { set +e; OUT=$("$@" 2>&1); STATUS=$?; set -e; }

run npm test
if [ "$STATUS" -eq 0 ]; then echo "  ok   tests pass"; else echo "  FAIL tests pass"; printf '%s\n' "$OUT" | tail -10; exit 1; fi

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

printf 'name,val\na,1\n"b""c\nd",2\n' >"$work/in.csv"
node src/cli.js csv2json "$work/in.csv" "$work/out.json"
if ! grep -q '"b\\"c' "$work/out.json"; then echo "  FAIL cli csv2json"; cat "$work/out.json"; exit 1; fi
echo "  ok   cli csv2json"

printf '[{"name":"x","val":3}]' >"$work/in.json"
node src/cli.js json2csv "$work/in.json" "$work/out.csv"
grep -q '^name,val$' "$work/out.csv"
echo "  ok   cli json2csv"

echo "smoke: PASS"