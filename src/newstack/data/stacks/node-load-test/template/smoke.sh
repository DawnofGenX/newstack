#!/usr/bin/env bash
# End-to-end checks: a real stub target, a real load run, real thresholds.
set -u

PORT="${PORT:-5471}"
BASE="http://127.0.0.1:${PORT}"
failures=0

pass() { printf 'ok %s\n' "$1"; }
fail() { printf 'FAIL %s\n' "$1"; failures=$((failures + 1)); }

if ! command -v node >/dev/null 2>&1; then
  echo "smoke: node is required" >&2
  exit 2
fi

if [ ! -f dist/src/main.js ] || [ ! -f dist/src/stub.js ]; then
  npm run build >/dev/null || { echo "smoke: build failed" >&2; exit 2; }
fi

if ss -ltn 2>/dev/null | grep -q "[:.]${PORT} "; then
  echo "smoke: port ${PORT} is already in use" >&2
  exit 2
fi

work="$(mktemp -d)"
trap 'kill "${stub_pid:-0}" 2>/dev/null; rm -rf "$work"' EXIT

node dist/src/stub.js --port "$PORT" >"$work/stub.log" 2>&1 &
stub_pid=$!

ready=0
for _ in $(seq 1 60); do
  if curl -fsS "${BASE}/ok" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 0.1
done
if [ "$ready" -eq 0 ]; then
  echo "smoke: the stub never came up" >&2
  cat "$work/stub.log" >&2
  exit 2
fi

# 1. A clean run passes its thresholds and reports the sample counts.
out="$(node dist/src/main.js run --target "${BASE}/ok" --requests 120 --warmup 8 \
  --json "$work/report.json" 2>&1)"
status=$?
if [ "$status" -eq 0 ] \
  && printf '%s' "$out" | grep -q '112 measured, 8 warm-up, 0 errors' \
  && printf '%s' "$out" | grep -q '^result     PASS$'; then
  pass "a clean run passes and counts 112 measured samples"
else
  fail "a clean run passes (exit ${status})"
  printf '%s\n' "$out"
fi

# 2. The JSON report is the artefact: counts, the percentile method, the verdict.
if node -e 'const r = require(process.argv[1]);
  const ok = r.summary.count === 112 && r.summary.method === "nearest-rank"
    && r.passed === true && r.samples.length === 120;
  process.exit(ok ? 0 : 1)' "$work/report.json" 2>/dev/null; then
  pass "the JSON report keeps 112 measured and 120 recorded samples"
else
  fail "the JSON report is complete"
fi

# 3. A failing target fails the default error-rate gate.
out="$(node dist/src/main.js run --target "${BASE}/flaky" --requests 40 --warmup 0 2>&1)"
status=$?
if [ "$status" -eq 1 ] && printf '%s' "$out" | grep -q 'FAILED' \
  && printf '%s' "$out" | grep -q '^result     FAIL (1 threshold(s))$'; then
  pass "a 503 fails the default errorRate gate with exit 1"
else
  fail "a 503 fails the default gate (exit ${status})"
  printf '%s\n' "$out"
fi

# 4. Replay is deterministic: 1..100 has p95 = 95 by nearest-rank.
node -e 'const fs = require("fs");
  fs.writeFileSync(process.argv[1], JSON.stringify({
    samples: Array.from({ length: 100 }, (_, i) => ({ latencyMs: i + 1 })),
  }));' "$work/samples.json"

out="$(node dist/src/main.js replay --samples "$work/samples.json" --threshold p95=95 2>&1)"
status=$?
if [ "$status" -eq 0 ] && printf '%s' "$out" | grep -q 'p95 95 '; then
  pass "replay computes p95 = 95 for 1..100 and passes p95=95"
else
  fail "replay p95 arithmetic (exit ${status})"
  printf '%s\n' "$out"
fi

out="$(node dist/src/main.js replay --samples "$work/samples.json" --threshold p95=94 2>&1)"
status=$?
if [ "$status" -eq 1 ] && printf '%s' "$out" | grep -q '^result     FAIL (1 threshold(s))$'; then
  pass "replay fails a threshold 1 ms too tight"
else
  fail "replay fails an impossible threshold (exit ${status})"
  printf '%s\n' "$out"
fi

# 5. A misspelled threshold is a usage error, never a silent pass.
out="$(node dist/src/main.js run --target "${BASE}/ok" --requests 10 --warmup 0 \
  --threshold p9=100 2>&1)"
status=$?
if [ "$status" -eq 2 ] && printf '%s' "$out" | grep -q 'unknown threshold'; then
  pass "a misspelled threshold exits 2"
else
  fail "a misspelled threshold exits 2 (exit ${status})"
  printf '%s\n' "$out"
fi

# 6. A refused connection is an error sample, and errors fail the gate.
out="$(node dist/src/main.js run --target http://127.0.0.1:9/ok --requests 2 --warmup 0 \
  --timeout 500 2>&1)"
status=$?
if [ "$status" -eq 1 ] && printf '%s' "$out" | grep -q 'errors (100.00%)'; then
  pass "a dead port counts every request as an error"
else
  fail "a dead port counts errors (exit ${status})"
  printf '%s\n' "$out"
fi

# 7. Warm-up that covers the whole run is refused, not silently empty.
out="$(node dist/src/main.js run --target "${BASE}/ok" --requests 3 --warmup 3 2>&1)"
status=$?
if [ "$status" -eq 2 ] && printf '%s' "$out" | grep -q 'would leave nothing measured'; then
  pass "a warm-up as long as the run exits 2"
else
  fail "a warm-up as long as the run exits 2 (exit ${status})"
  printf '%s\n' "$out"
fi

# 8. A missing samples file is a usage error.
out="$(node dist/src/main.js replay --samples "$work/nope.json" --threshold p95=1 2>&1)"
status=$?
if [ "$status" -eq 2 ] && printf '%s' "$out" | grep -q 'cannot read'; then
  pass "a missing samples file exits 2"
else
  fail "a missing samples file exits 2 (exit ${status})"
  printf '%s\n' "$out"
fi

# 9. help works without a target, and the stub is still healthy afterwards.
if node dist/src/main.js --help 2>&1 | grep -q '^usage:'; then
  pass "help prints usage"
else
  fail "help prints usage"
fi
if curl -fsS "${BASE}/ok" >/dev/null 2>&1; then
  pass "the stub is still healthy after every run"
else
  fail "the stub is still healthy after every run"
fi

if [ "$failures" -ne 0 ]; then
  printf 'smoke: %d check(s) failed\n' "$failures" >&2
  exit 1
fi
printf 'smoke: all checks passed\n'
