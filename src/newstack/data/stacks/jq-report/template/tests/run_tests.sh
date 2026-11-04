#!/usr/bin/env bash
# Run every suite. Designed to be called as "tests/run_tests.sh" from anywhere.
set -u

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
readonly ROOT
readonly BIN="$ROOT/bin/{{ npm_name }}"
readonly PROG='{{ npm_name }}'
readonly DATA="$ROOT/data/sample.json"
TMP=$(mktemp -d)
readonly TMP
trap 'rm -rf "$TMP"' EXIT
readonly ERRFILE="$TMP/stderr"
: >"$ERRFILE"

# shellcheck source=tests/harness.sh
. "$ROOT/tests/harness.sh"
# shellcheck source=tests/filters_test.sh
. "$ROOT/tests/filters_test.sh"
# shellcheck source=tests/cli_test.sh
. "$ROOT/tests/cli_test.sh"

suite_filters
suite_cli

report
