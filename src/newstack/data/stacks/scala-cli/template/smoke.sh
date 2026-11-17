#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

run() {
  set +e
  OUT=$("$@" 2>&1)
  STATUS=$?
  set -e
}

if ! command -v scala-cli >/dev/null 2>&1; then
  echo "smoke: scala-cli is missing (install scala-cli)"
  exit 1
fi
if ! command -v java >/dev/null 2>&1; then
  echo "smoke: java is missing (install java)"
  exit 1
fi

echo "smoke: scala-cli"

run scala-cli compile . --server=false
if [ "$STATUS" -eq 0 ]; then ok "scala compile"; else bad "scala compile"; printf '%s\n' "$OUT" | tail -8; fi

run scala-cli test . --server=false
if [ "$STATUS" -eq 0 ]; then ok "scala test"; else bad "scala test"; printf '%s\n' "$OUT" | tail -8; fi

run ./bin/{{ npm_name }} --help
if [ "$STATUS" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; printf '%s\n' "$OUT" | tail -8; fi

set +e
./bin/{{ npm_name }} --bogus >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 2 ]; then ok "usage error exits 2"; else bad "usage error exits 2"; fi

set +e
./bin/{{ npm_name }} does-not-exist.txt >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 1 ]; then ok "missing file exits 1"; else bad "missing file exits 1"; fi

run sh -c "printf 'alpha beta\\ngamma delta\\n' > .p1.txt && printf 'no trailing newline' > .p2.txt && printf 'h\\303\\251llo w\\303\\266rld\\n' > .p3.txt && : > .p4.txt && for f in .p1.txt .p2.txt .p3.txt .p4.txt; do ours=\$(./bin/{{ npm_name }} -l -w -c \"\$f\" | awk '{print \$1, \$2, \$3}'); theirs=\$(wc -l -w -c \"\$f\" | awk '{print \$1, \$2, \$3}'); if [ \"\$ours\" != \"\$theirs\" ]; then echo \"MISMATCH \$f: ours=[\$ours] theirs=[\$theirs]\"; exit 1; fi; done && rm -f .p1.txt .p2.txt .p3.txt .p4.txt && echo parity ok"
if [ "$STATUS" -eq 0 ]; then ok "parity with wc"; else bad "parity with wc"; printf '%s\n' "$OUT" | tail -8; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]