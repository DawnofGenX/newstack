#!/usr/bin/env bash
set -u

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
readonly ROOT
readonly CHECK="$ROOT/tools/check-links.sh"
TMP=$(mktemp -d)
readonly TMP
trap 'rm -rf "$TMP"' EXIT
readonly ERRFILE="$TMP/stderr"
: >"$ERRFILE"

# shellcheck source=tests/harness.sh
. "$ROOT/tests/harness.sh"
# shellcheck source=tests/check_links_test.sh
. "$ROOT/tests/check_links_test.sh"

suite_checker
suite_book

report
