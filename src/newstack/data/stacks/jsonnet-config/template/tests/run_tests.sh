#!/usr/bin/env bash
# Runs the Jsonnet test suite and turns its report into an exit code.
set -uo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
report="$(jsonnet -S -J "$root/lib" -J "$root/tests" "$root/tests/suite.jsonnet")"
status=$?
printf '%s\n' "$report"
[ "$status" -eq 0 ] || exit 1
grep -q 'failed: 0$' <<<"$report" || exit 1
