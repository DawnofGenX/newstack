#!/usr/bin/env bash
# The CLI's contract is exit codes, stdout/stderr, and what a pipeline does to it.
#
# Deliberately not `set -e`: a smoke test that dies on the first failure reports one
# symptom instead of the whole list.
set -uo pipefail

cd "$(dirname "$0")"
NODE="${NODE:-node}"
ENTRY="dist/src/{{ package_name }}/main.js"

if [ ! -f "$ENTRY" ]; then
  echo "smoke: build first (npm run build)" >&2
  exit 1
fi

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
failures=0

check() {
  local name="$1" status="$2"
  if [ "$status" -eq 0 ]; then
    printf 'ok   %s\n' "$name"
  else
    printf 'FAIL %s\n' "$name"
    failures=$((failures + 1))
  fi
}

# Compare two values and report the difference instead of just "failed".
check_equal() {
  local name="$1" want="$2" got="$3"
  if [ "$want" = "$got" ]; then
    check "$name" 0
  else
    printf 'FAIL %s (got %s, want %s)\n' "$name" "$got" "$want"
    failures=$((failures + 1))
  fi
}

check_match() {
  local name="$1" pattern="$2" file="$3"
  if grep -qE "$pattern" "$file"; then check "$name" 0; else check "$name" 1; fi
}

json_field() {
  "$NODE" -e '
    const fs = require("node:fs");
    const report = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
    const value = process.argv[2].split(".").reduce((node, key) => node[key], report);
    console.log(value);' "$1" "$2"
}

printf 'hello world\nbye\n' >"$work/two.txt"
printf 'a\nb' >"$work/no-newline.txt"
printf 'a\r\nb\r\n' >"$work/crlf.txt"
printf 'h\xc3\xa9llo\n' >"$work/multibyte.txt"
: >"$work/empty.txt"
for i in $(seq 1 200000); do printf 'line %d of a long file\n' "$i"; done >"$work/big.txt"

"$NODE" "$ENTRY" "$work/two.txt" >"$work/out.txt" 2>"$work/err.txt"
check_equal "a counted file exits 0" 0 $?
check_match "the table names the file" '^[[:space:]]*2[[:space:]]+3[[:space:]]+16[[:space:]]+.*two\.txt$' "$work/out.txt"
check_equal "and writes nothing to stderr" "" "$(cat "$work/err.txt")"

"$NODE" "$ENTRY" "$work/no-newline.txt" >"$work/out.txt"
check_match "a last line without a newline is a line" '^[[:space:]]*2[[:space:]]+2[[:space:]]+3' "$work/out.txt"

"$NODE" "$ENTRY" --json "$work/no-newline.txt" >"$work/report.json"
check_equal "the no-newline file has two lines" 2 "$(json_field "$work/report.json" total.lines)"
"$NODE" "$ENTRY" --json "$work/crlf.txt" >"$work/report.json"
check_equal "crlf is two lines, not four" 2 "$(json_field "$work/report.json" total.lines)"
"$NODE" "$ENTRY" --json "$work/multibyte.txt" >"$work/report.json"
check_equal "bytes are utf-8 bytes (7, not 6 characters)" 7 "$(json_field "$work/report.json" total.bytes)"

printf 'one two three\n' | "$NODE" "$ENTRY" >"$work/out.txt"
check_match "standard input is read when no file is named" '^[[:space:]]*1[[:space:]]+3[[:space:]]+14' "$work/out.txt"
printf 'one two\n' | "$NODE" "$ENTRY" - >"$work/out.txt"
check_match "a piped - is standard input" '^[[:space:]]*1[[:space:]]+2[[:space:]]+8' "$work/out.txt"

"$NODE" "$ENTRY" "$work/two.txt" "$work/no-newline.txt" >"$work/out.txt"
check_match "several files get a total row" '^[[:space:]]*4[[:space:]]+5[[:space:]]+19[[:space:]]+total$' "$work/out.txt"

"$NODE" "$ENTRY" "$work/missing.txt" >"$work/out.txt" 2>"$work/err.txt"
check_equal "an unreadable file exits 1" 1 $?
check_match "and says why on stderr" 'ENOENT' "$work/err.txt"

"$NODE" "$ENTRY" --nope >"$work/out.txt" 2>"$work/err.txt"
check_equal "an unknown flag exits 2" 2 $?
check_match "and prints the usage text" 'usage:' "$work/err.txt"

"$NODE" "$ENTRY" --fail-empty "$work/empty.txt" >"$work/out.txt" 2>"$work/err.txt"
check_equal "--fail-empty turns zero lines into exit 1" 1 $?
check_match "and names the gate, not a silent success" 'no lines counted' "$work/err.txt"

# The pipeline case: head closes the pipe while we are still writing to it.
"$NODE" "$ENTRY" "$work/big.txt" 2>"$work/err.txt" | head -1 >"$work/out.txt"
codes=("${PIPESTATUS[@]}")
check_equal "piping into head -1 is not an error" 0 "${codes[0]}"
check_equal "and prints no stack trace" "" "$(cat "$work/err.txt")"
check_match "while the reader still gets the header" '^[[:space:]]*lines[[:space:]]+words[[:space:]]+bytes[[:space:]]*$' "$work/out.txt"

"$NODE" "$ENTRY" --selftest >"$work/out.txt"
check_equal "the selftest passes" 0 $?
check_match "and says how many checks ran" '[0-9]+ checks passed' "$work/out.txt"

"$NODE" "$ENTRY" --version >"$work/out.txt"
check_equal "--version exits 0" 0 $?
check_match "and prints a version" '^[^ ]+ [0-9]+\.[0-9]+\.[0-9]+$' "$work/out.txt"

if [ "$failures" -ne 0 ]; then
  printf 'smoke: %d check(s) failed\n' "$failures"
  exit 1
fi
printf 'smoke: all checks passed\n'
