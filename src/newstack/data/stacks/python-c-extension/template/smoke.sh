#!/usr/bin/env bash
# Build the extension, then use it the way a reader would.
set -euo pipefail

cd "$(dirname "$0")"
PY=${PY:-.venv/bin/python}

uv venv -q --allow-existing .venv
uv pip install -q --python "$PY" -e .

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

printf 'alpha beta\ngamma' > "$work/three.txt"
printf 'h\xc3\xa9llo w\xc3\xb6rld\n' > "$work/utf8.txt"
: > "$work/empty.txt"

check() {
    local name=$1 want=$2 got=$3
    if [ "$got" != "$want" ]; then
        echo "FAIL $name: want [$want] got [$got]" >&2
        exit 1
    fi
    echo "ok $name"
}

check three "$("$PY" -m {{ package_name }}.cli "$work/three.txt")" '{"lines": 1, "words": 3, "bytes": 16}'
check utf8 "$("$PY" -m {{ package_name }}.cli "$work/utf8.txt")" '{"lines": 1, "words": 2, "bytes": 14}'
check empty "$("$PY" -m {{ package_name }}.cli "$work/empty.txt")" '{"lines": 0, "words": 0, "bytes": 0}'
check stdin "$(printf 'a b' | "$PY" -m {{ package_name }}.cli -)" '{"lines": 0, "words": 2, "bytes": 3}'

"$PY" - <<'PY'
import sys

import {{ package_name }}
from {{ package_name }} import reference

shared = {{ package_name }}._speedups.__file__
assert shared.endswith((".so", ".pyd")), shared
for size in range(0, 200):
    data = bytes((i * 37) % 256 for i in range(size))
    assert {{ package_name }}.count_bytes(data) == reference.count_bytes(data), size
print("ok the extension agrees with the reference on 200 inputs")
PY

echo "smoke: all checks passed"
