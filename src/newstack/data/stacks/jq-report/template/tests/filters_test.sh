#!/usr/bin/env bash
# The expected strings below were written down by hand from data/sample.json,
# not captured from the tool: a filter that changes its answer has to be a
# deliberate edit to this file as well.

suite_filters() {
  local filter

  while IFS= read -r filter; do
    run_capture "$BIN" run "$filter" "$DATA"
    check "run $filter exits 0" 0 "$STATUS"
    check "run $filter prints one line" 1 "$(printf '%s\n' "$OUT" | grep -c '')"
  done <<'FILTERS'
status-counts
top-paths
slowest
bytes-by-day
error-rate
FILTERS

  run_capture "$BIN" run status-counts "$DATA"
  check "status-counts counts each code" \
    '[{"status":200,"requests":3},{"status":201,"requests":1},{"status":404,"requests":1},{"status":500,"requests":1}]' \
    "$OUT"

  run_capture "$BIN" run top-paths "$DATA"
  check "top-paths sorts by hits" \
    '[{"path":"/api/items","hits":3},{"path":"/","hits":2},{"path":"/missing","hits":1}]' \
    "$OUT"

  run_capture "$BIN" run slowest "$DATA"
  check "slowest lists five requests, slowest first" \
    '[{"method":"POST","path":"/api/items","ms":240},{"method":"POST","path":"/api/items","ms":57},{"method":"GET","path":"/api/items","ms":38},{"method":"GET","path":"/","ms":12},{"method":"GET","path":"/","ms":11}]' \
    "$OUT"

  run_capture "$BIN" run bytes-by-day "$DATA"
  check "bytes-by-day adds bytes per day" \
    '[{"day":"2026-11-01","bytes":2688},{"day":"2026-11-02","bytes":908}]' \
    "$OUT"

  run_capture "$BIN" run error-rate "$DATA"
  check "error-rate reports one failure in six" \
    '{"total":6,"errors":1,"error_rate":16.7}' "$OUT"

  # The CLI must not be doing anything the plain jq invocation would not.
  check "the filter alone gives the same answer" \
    "$OUT" "$(jq -c -f "$ROOT/filters/error-rate.jq" "$DATA")"

  # A filter must not be tied to the sample file.
  cat >"$TMP/other.json" <<'JSON'
[
  {"time":"2025-01-01T00:00:00Z","method":"GET","path":"/a","status":500,"bytes":10,"ms":1},
  {"time":"2025-01-02T00:00:00Z","method":"GET","path":"/a","status":500,"bytes":20,"ms":2},
  {"time":"2025-01-02T00:00:00Z","method":"GET","path":"/b","status":200,"bytes":30,"ms":3}
]
JSON
  run_capture "$BIN" run top-paths "$TMP/other.json"
  check "top-paths on a different log" '[{"path":"/a","hits":2},{"path":"/b","hits":1}]' "$OUT"
  run_capture "$BIN" run error-rate "$TMP/other.json"
  check "error-rate on a different log" '{"total":3,"errors":2,"error_rate":66.7}' "$OUT"
  run_capture "$BIN" run bytes-by-day "$TMP/other.json"
  check "bytes-by-day on a different log" \
    '[{"day":"2025-01-01","bytes":10},{"day":"2025-01-02","bytes":50}]' "$OUT"

  # Empty input is a normal day with no traffic, not an error.
  printf '[]\n' >"$TMP/empty.json"
  run_capture "$BIN" run top-paths "$TMP/empty.json"
  check "top-paths on an empty log" '[]' "$OUT"
  check "top-paths on an empty log exits 0" 0 "$STATUS"
  run_capture "$BIN" run error-rate "$TMP/empty.json"
  check "error-rate on an empty log divides by nothing" \
    '{"total":0,"errors":0,"error_rate":0}' "$OUT"
}
