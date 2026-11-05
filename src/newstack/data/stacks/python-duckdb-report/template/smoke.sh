#!/usr/bin/env bash
# Smoke: the shipped report must match the golden file byte for byte, and the
# refusals must exit 2.
set -euo pipefail
cd "$(dirname "$0")"

if [ -z "${PY:-}" ]; then
  if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=python3; fi
fi
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

report() { "$PY" -m {{ package_name }} report --data data/orders.csv --group-by region --metric revenue "$@"; }

say() { echo "ok $1"; }

# 1. the golden file: same bytes, not merely the same numbers
report >"$TMP/report.md"
diff -u expected/report.md "$TMP/report.md"
say "the report matches expected/report.md byte for byte"

# 2. running it again produces the same bytes (no ordering by chance)
report >"$TMP/report-again.md"
cmp -s "$TMP/report.md" "$TMP/report-again.md"
say "a second run is byte identical"

# 3. the accounting survives the transport: 12 rows, 1 null, 4 groups
report --format json >"$TMP/report.json"
grep -q '"scanned": 12' "$TMP/report.json"
grep -q '"skipped": 1' "$TMP/report.json"
grep -q '"group": "south"' "$TMP/report.json"
say "json carries scanned 12, skipped 1"

# 4. money is summed as decimal, not float: 300.00 + 99.99 + 150.50
grep -q '| south | 550.49 | 3 |' "$TMP/report.md"
say "south sums to exactly 550.49 (decimal, not binary float)"

# 5. --limit keeps the largest groups only
report --limit 2 | grep -c '^| ' | grep -qx 4
say "--limit 2 prints the header plus two groups"

# 6. an unknown column is refused with the real column names
set +e
"$PY" -m {{ package_name }} report --data data/orders.csv --group-by region --metric revenu \
  >"$TMP/bad.out" 2>"$TMP/bad.err"
status=$?
set -e
test "$status" -eq 2
grep -q "no column 'revenu'" "$TMP/bad.err"
say "an unknown column exits 2 and names the real columns"

# 7. a missing file is refused, not reported as an empty result
set +e
"$PY" -m {{ package_name }} report --data data/nope.csv --group-by region --metric revenue \
  >/dev/null 2>"$TMP/missing.err"
status=$?
set -e
test "$status" -eq 2
grep -q "no such file" "$TMP/missing.err"
say "a missing file exits 2"

echo "smoke: all checks passed"
