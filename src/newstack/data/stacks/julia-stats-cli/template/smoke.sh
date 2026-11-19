#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

if ! command -v julia >/dev/null 2>&1; then
  case "julia" in
    guile-json|lua-socket|lua-cjson|fp-units-fcl) : ;;
    *) echo "smoke: julia is missing (install julia)"; exit 1 ;;
  esac
fi

echo "smoke: julia-cli"

if (
JULIA_PKG_OFFLINE=true julia --project=. -e 'using Pkg; Pkg.instantiate(); Pkg.precompile()'
); then ok "instantiate"; else bad "instantiate"; fi

if (
julia --project=. test/runtests.jl
); then ok "test"; else bad "test"; fi

if (
julia --project=. bin/textstat.jl --help >/dev/null; test $? -eq 0
); then ok "help"; else bad "help"; fi

if (
julia --project=. bin/textstat.jl --bogus >/dev/null 2>&1; test $? -eq 2
); then ok "usage-error"; else bad "usage-error"; fi

if (
julia --project=. bin/textstat.jl does-not-exist.txt >/dev/null 2>&1; test $? -eq 1
); then ok "missing-file"; else bad "missing-file"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
