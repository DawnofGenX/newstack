#!/usr/bin/env bash
# Prove the harness end to end: score a run, write a record, and diff two of them.
set -euo pipefail

cd "$(dirname "$0")"

PY=${PY:-python3}
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

check() { printf 'ok %s\n' "$1"; }
fail() { printf 'FAIL %s\n' "$1" >&2; exit 1; }

"$PY" -m {{ package_name }} run --data data/dev.jsonl --predictions data/predictions.good.jsonl \
  --out "$work/good.json" --run-id good >"$work/good.txt"
grep -q '^score     0.9167$' "$work/good.txt" || fail "good run should score 0.9167"
check "good run"

"$PY" -m {{ package_name }} run --data data/dev.jsonl --predictions data/predictions.bad.jsonl \
  --out "$work/bad.json" --run-id bad >"$work/bad.txt"
grep -q '^answered  3/4$' "$work/bad.txt" || fail "bad run should answer 3 of 4"
grep -q '^missing   1: word-4$' "$work/bad.txt" || fail "the unanswerred id should be listed"
check "bad run keeps the missing id visible"

set +e
"$PY" -m {{ package_name }} compare --baseline "$work/good.json" --candidate "$work/bad.json" >"$work/cmp.txt"
status=$?
set -e
test "$status" -eq 1 || fail "a regression must exit 1, got $status"
grep -q '^regressed 4$' "$work/cmp.txt" || fail "four ids should regress"
check "compare reports the regression"

set +e
"$PY" -m {{ package_name }} compare --baseline "$work/bad.json" --candidate "$work/good.json" >/dev/null
status=$?
set -e
test "$status" -eq 0 || fail "an improvement must exit 0, got $status"
check "compare accepts an improvement"

set +e
"$PY" -m {{ package_name }} run --data data/dev.jsonl --predictions data/nope.jsonl >/dev/null 2>"$work/err.txt"
status=$?
set -e
test "$status" -eq 2 || fail "a missing file must exit 2, got $status"
grep -q 'cannot read' "$work/err.txt" || fail "the error should say cannot read"
check "missing file exits 2"

printf '{"id":"cap-1","prediction":"Paris"}\n' | "$PY" -m {{ package_name }} run --data data/dev.jsonl --predictions - >"$work/stdin.txt"
grep -q '^answered  1/4$' "$work/stdin.txt" || fail "stdin predictions should be read"
check "predictions can come from stdin"

printf 'smoke: all checks passed\n'
