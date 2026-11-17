#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

if ! command -v node >/dev/null 2>&1; then
  case "node" in
    guile-json|lua-socket|lua-cjson|fp-units-fcl) : ;;
    *) echo "smoke: node is missing (install node)"; exit 1 ;;
  esac
fi
if ! command -v npm >/dev/null 2>&1; then
  case "npm" in
    guile-json|lua-socket|lua-cjson|fp-units-fcl) : ;;
    *) echo "smoke: npm is missing (install npm)"; exit 1 ;;
  esac
fi
if ! command -v git >/dev/null 2>&1; then
  :
fi

echo "smoke: next-app-ts"

if (
npm install --no-audit --no-fund
); then ok "install"; else bad "install"; fi

if (
npm run typecheck
); then ok "typecheck"; else bad "typecheck"; fi

if (
npm test
); then ok "test"; else bad "test"; fi

if (
npm run build
); then ok "build"; else bad "build"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
