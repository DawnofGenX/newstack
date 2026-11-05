#!/usr/bin/env bash
# End-to-end smoke: a stub endpoint, one permanent failure, and a resume.
set -euo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-5468}"
PY="${PY:-python3}"
BASE="http://127.0.0.1:$PORT/v1"
TMP="$(mktemp -d)"
SERVER=""

cleanup() {
  if [ -n "$SERVER" ]; then
    kill -TERM "$SERVER" 2>/dev/null || true
    wait "$SERVER" 2>/dev/null || true
  fi
  rm -rf "$TMP"
}
trap cleanup EXIT

if ss -ltn 2>/dev/null | grep -q ":$PORT "; then
  echo "port $PORT is already answering - stop that process before running smoke" >&2
  exit 1
fi

"$PY" tests/stub.py --port "$PORT" --flaky-after 1 >"$TMP/stub.log" 2>&1 &
SERVER=$!
for _ in $(seq 1 100); do
  if grep -q "listening on" "$TMP/stub.log" 2>/dev/null; then break; fi
  sleep 0.1
done
grep -q "listening on" "$TMP/stub.log" || { echo "the stub never started" >&2; cat "$TMP/stub.log" >&2; exit 1; }

say() { echo "ok $1"; }

# 1. a clean batch exits 0 and answers every request
set +e
"$PY" -m {{ package_name }} run --requests data/requests.jsonl --out "$TMP/clean.jsonl" \
  --base-url "$BASE" >"$TMP/clean.out" 2>&1
status=$?
set -e
test "$status" -eq 0 || { cat "$TMP/clean.out" >&2; echo "FAIL clean batch exited $status" >&2; exit 1; }
grep -q "^ok        3$" "$TMP/clean.out"
test "$(wc -l <"$TMP/clean.jsonl")" -eq 3
say "clean batch exits 0 with 3 answers"

# 2. the retry is visible in the record: the 429 prompt took two attempts
grep '"id": "flaky-3"' "$TMP/clean.jsonl" | grep -q '"attempts": 2'
say "a 429 was retried (attempts 2 in the record)"

# 3. a permanent failure exits 1, is named on stdout, and still keeps the answers
set +e
"$PY" -m {{ package_name }} run --requests data/requests.with-failure.jsonl \
  --out "$TMP/mixed.jsonl" --base-url "$BASE" >"$TMP/mixed.out" 2>&1
status=$?
set -e
test "$status" -eq 1 || { cat "$TMP/mixed.out" >&2; echo "FAIL mixed batch exited $status" >&2; exit 1; }
grep -q "^failed    1$" "$TMP/mixed.out"
grep -q "^failure   bad-4: http 400$" "$TMP/mixed.out"
test "$(wc -l <"$TMP/mixed.jsonl")" -eq 3
say "a permanent 400 exits 1, is named, and the other two answers survive"

# 4. a rerun resumes: nothing is sent twice and the file does not grow
set +e
"$PY" -m {{ package_name }} run --requests data/requests.jsonl --out "$TMP/clean.jsonl" \
  --base-url "$BASE" >"$TMP/resumed.out" 2>&1
status=$?
set -e
test "$status" -eq 0
grep -q "^resumed   3$" "$TMP/resumed.out"
test "$(wc -l <"$TMP/clean.jsonl")" -eq 3
say "a rerun resumes all 3 and writes nothing new"

# 5. an unreadable batch exits 2 instead of looking like a clean run
set +e
"$PY" -m {{ package_name }} run --requests data/nope.jsonl --out "$TMP/nope.jsonl" \
  --base-url "$BASE" >"$TMP/nope.out" 2>&1
status=$?
set -e
test "$status" -eq 2 || { cat "$TMP/nope.out" >&2; echo "FAIL missing batch exited $status" >&2; exit 1; }
grep -q "cannot read" "$TMP/nope.out"
say "a missing requests file exits 2"

echo "smoke: all checks passed"
