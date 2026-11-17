#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

if ! command -v elixir >/dev/null 2>&1; then
  case "elixir" in
    guile-json|lua-socket|lua-cjson|fp-units-fcl) : ;;
    *) echo "smoke: elixir is missing (install elixir)"; exit 1 ;;
  esac
fi
if ! command -v mix >/dev/null 2>&1; then
  case "mix" in
    guile-json|lua-socket|lua-cjson|fp-units-fcl) : ;;
    *) echo "smoke: mix is missing (install mix)"; exit 1 ;;
  esac
fi

echo "smoke: elixir-mix-cli"

if (
mix deps.get
); then ok "deps"; else bad "deps"; fi

if (
mix format --check-formatted
); then ok "format"; else bad "format"; fi

if (
mix test
); then ok "test"; else bad "test"; fi

if (
MIX_ENV=prod mix escript.build && ./{{ npm_name }} --help >/dev/null
); then ok "escript"; else bad "escript"; fi

if (
./{{ npm_name }} --bogus >/dev/null 2>&1; test $? -eq 2
); then ok "usage-error"; else bad "usage-error"; fi

if (
./{{ npm_name }} does-not-exist.txt >/dev/null 2>&1; test $? -eq 1
); then ok "missing-file"; else bad "missing-file"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
