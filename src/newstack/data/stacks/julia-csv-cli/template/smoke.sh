#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

if ! command -v julia >/dev/null 2>&1; then
  echo "smoke: julia is missing (install julia)"
  exit 1
fi

echo "smoke: {{ package_name }}"

if (
JULIA_PKG_OFFLINE=true julia --project=. -e 'using Pkg; Pkg.instantiate(); Pkg.precompile()'
); then ok "instantiate"; else bad "instantiate"; fi

if (
julia --project=. test/runtests.jl
); then ok "test"; else bad "test"; fi

if (
julia --project=. bin/{{ npm_name }}.jl --help >/dev/null
); then ok "help exits 0"; else bad "help exits 0"; fi

set +e
OUT=$(printf 'a,b\n1,2\n' | julia --project=. bin/{{ npm_name }}.jl --json)
STATUS=$?
set -e
if [ "$OUT" = '[{"a":"1","b":"2"}]' ]; then ok "json output"; else bad "json output"; printf '       got: %s\n' "$OUT"; fi

set +e
OUT=$(printf 'name,score\nalice,10\nbob,7\n' | julia --project=. bin/{{ npm_name }}.jl --summary score)
STATUS=$?
set -e
if printf '%s\n' "$OUT" | grep -qx 'mean=8.5'; then ok "summary mean"; else bad "summary mean"; printf '       got: %s\n' "$OUT"; fi

if (
julia --project=. bin/{{ npm_name }}.jl --bogus >/dev/null 2>&1; test $? -eq 2
); then ok "usage error exits 2"; else bad "usage error exits 2"; fi

if (
julia --project=. bin/{{ npm_name }}.jl no-such-file.csv >/dev/null 2>&1; test $? -eq 1
); then ok "missing file exits 1"; else bad "missing file exits 1"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
