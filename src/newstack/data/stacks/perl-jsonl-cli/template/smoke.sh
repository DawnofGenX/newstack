#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

CLI="perl bin/{{ npm_name }}"
DATA=$(mktemp)
TMP=$(mktemp)
trap 'rm -f "$DATA" "$TMP"' EXIT

cat > "$DATA" <<'JSONL'
{"id":1,"user":{"name":"ada"},"score":10,"tags":["math"]}
{"id":2,"user":{"name":"bob"},"score":9.5,"tags":[]}
{"id":3,"user":{"name":"cy"},"score":30}
JSONL

echo "smoke: {{ package_name }}"

check() {
  if [ "$2" = "$3" ]; then
    ok "$1"
  else
    bad "$1"
    printf '       expected: %s\n       actual:   %s\n' "$2" "$3"
  fi
}

check "help exits 0" "0" "$(sh -c "$CLI --help >/dev/null 2>&1; echo \$?")"
check "version" "0.01" "$($CLI --version)"
check "counts every record" "3" "$($CLI --count "$DATA")"
check "re-emits canonical json" '{"id":2,"score":9.5,"tags":[],"user":{"name":"bob"}}' "$($CLI "$DATA" | sed -n 2p)"
check "projects nested paths" '{"id":1,"user":{"name":"ada"}}' "$($CLI -f id,user.name "$DATA" | sed -n 1p)"
check "filters with --gt" "2" "$($CLI --where score --gt 9.9 --count "$DATA")"
check "filters with --match" "1" "$($CLI --where user.name --match '^c' --count "$DATA")"
check "sorts numerically" "9.5" "$($CLI --sort score --numeric "$DATA" | sed -n 1p | sed 's/.*"score":\([0-9.]*\).*/\1/')"
check "sorts with --reverse" "30" "$($CLI --sort score --numeric --reverse "$DATA" | sed -n 1p | sed 's/.*"score":\([0-9.]*\).*/\1/')"
check "stats" "count=3 sum=49.5 mean=16.5 min=9.5 max=30" "$($CLI --stats score "$DATA")"
check "usage error exits 2" "2" "$(sh -c "$CLI --bogus 2>/dev/null; echo \$?")"
check "missing file exits 1" "1" "$(sh -c "$CLI does-not-exist.jsonl 2>/dev/null; echo \$?")"

printf '{"a":1}\nnot json\n' > "$TMP"
check "bad json names the line" "2" "$(sh -c "$CLI '$TMP' 2>&1 >/dev/null | sed -n 's/.*line \([0-9]*\).*/\1/p'")"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
