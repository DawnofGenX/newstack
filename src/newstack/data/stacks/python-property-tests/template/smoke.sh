#!/usr/bin/env bash
# Prove the generated project works without pytest reading the test files: the CLI
# answers, the demo finds the documented counterexample, and a bad interval is
# refused rather than silently reinterpreted.
set -euo pipefail

if [ -z "${PY:-}" ]; then
  if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=python3; fi
fi

run() { "$PY" -m {{ package_name }} "$@"; }

check() { printf 'ok %s\n' "$1"; }

test "$(run cover 0 2 1 3)" = "3"
check "cover counts an overlap once"

test "$(run cover 0 1 1 2 2 3)" = "3"
check "cover merges touching runs"

run demo > demo.txt
grep -q '^smallest input that fools a naive sum: \[0, 1), \[0, 1)$' demo.txt
grep -q '^naive sum 2   real coverage 1$' demo.txt
check "demo finds the minimal counterexample"

run demo > demo2.txt
cmp -s demo.txt demo2.txt
check "demo is deterministic"
rm -f demo.txt demo2.txt

set +e
run cover 5 2 > /dev/null 2>&1
status=$?
set -e
test "$status" -eq 2
check "a backwards interval exits 2"

set +e
run cover 0 > /dev/null 2>&1
status=$?
set -e
test "$status" -eq 2
check "an unpaired bound exits 2"

"$PY" -m pytest -q > /dev/null
check "pytest suite passes"

run --selftest > selftest.txt
grep -q 'checks passed' selftest.txt
rm -f selftest.txt
check "selftest passes"

printf 'smoke: all checks passed\n'
