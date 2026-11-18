#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

if ! command -v dart >/dev/null 2>&1; then
  echo "smoke: dart is missing (install dart)"
  exit 1
fi

echo "smoke: dart-json-canonical-cli"

printf '{"b": 2, "a": [3, 1], "C": {"z": null, "y": true}}' > "$work/input.json"

if (dart pub get); then ok "get"; else bad "get"; fi
if (dart analyze --fatal-infos); then ok "analyze"; else bad "analyze"; fi
if (dart test); then ok "test"; else bad "test"; fi
if (dart run bin/{{ npm_name }}.dart --help >/dev/null); then ok "help"; else bad "help"; fi

got=$(dart run bin/{{ npm_name }}.dart "$work/input.json")
want='{"C":{"y":true,"z":null},"a":[3,1],"b":2}'
if [ "$got" = "$want" ]; then ok "canonical output"; else bad "canonical output"; printf '       got: %s\n' "$got"; fi

got=$(printf '{"b":1,"a":2}' | dart run bin/{{ npm_name }}.dart)
if [ "$got" = '{"a":2,"b":1}' ]; then ok "stdin"; else bad "stdin"; printf '       got: %s\n' "$got"; fi

if (dart run bin/{{ npm_name }}.dart --check "$work/input.json" >/dev/null 2>&1; test $? -eq 1); then
  ok "--check rejects unsorted input"
else
  bad "--check rejects unsorted input"
fi

printf '{"a":2,"b":1}' > "$work/canonical.json"
if (dart run bin/{{ npm_name }}.dart --check "$work/canonical.json" >/dev/null); then
  ok "--check accepts canonical input"
else
  bad "--check accepts canonical input"
fi

if (dart run bin/{{ npm_name }}.dart --bogus >/dev/null 2>&1; test $? -eq 2); then ok "usage error exits 2"; else bad "usage error exits 2"; fi
if (dart run bin/{{ npm_name }}.dart no-such-file.json >/dev/null 2>&1; test $? -eq 1); then ok "missing file exits 1"; else bad "missing file exits 1"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
