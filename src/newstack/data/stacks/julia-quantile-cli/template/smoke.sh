#!/bin/sh
set -eu
FAILED=0
PASS=0
check() { if "$@" >/dev/null 2>&1; then PASS=$((PASS+1)); else FAILED=$((FAILED+1)); echo "FAIL: $*"; fi; }
printf '1\n2\n3\n4\n' > /tmp/q.txt
check julia --project=. test/runtests.jl
check julia --project=. bin/{{ npm_name }}.jl /tmp/q.txt
check sh -c "julia --project=. bin/{{ npm_name }}.jl /tmp/q.txt | grep -q 2.5"
check sh -c "julia --project=. bin/{{ npm_name }}.jl --mean /tmp/q.txt | grep -q 2.5"
check julia --project=. bin/{{ npm_name }}.jl --help
printf 'smoke: %d passed, %d failed\n' "$PASS" "$FAILED"
[ "$FAILED" -eq 0 ]
