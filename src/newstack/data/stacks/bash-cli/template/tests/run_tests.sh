#!/usr/bin/env bash
# tests/run_tests.sh -- run every suite and report one tally.
set -uo pipefail

# Byte semantics everywhere, exactly as the entry point sets it.
export LC_ALL=C

TESTS_ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)

# shellcheck source=../lib/counts.sh
. "$TESTS_ROOT/lib/counts.sh"
# shellcheck source=../lib/options.sh
. "$TESTS_ROOT/lib/options.sh"
# shellcheck source=../lib/runner.sh
. "$TESTS_ROOT/lib/runner.sh"
# shellcheck source=harness.sh
. "$TESTS_ROOT/tests/harness.sh"
# shellcheck source=counts_test.sh
. "$TESTS_ROOT/tests/counts_test.sh"
# shellcheck source=options_test.sh
. "$TESTS_ROOT/tests/options_test.sh"
# shellcheck source=runner_test.sh
. "$TESTS_ROOT/tests/runner_test.sh"

TESTS_TMP=$TESTS_ROOT/.test-tmp
rm -rf "$TESTS_TMP"
mkdir -p "$TESTS_TMP"

# Fixtures. printf, not here-documents: the escapes have to be real bytes.
printf 'alpha beta\ngamma delta\n' > "$TESTS_TMP/p1.txt"
printf 'alpha\nbeta\ngamma' > "$TESTS_TMP/p2.txt"
printf 'h\303\251llo w\303\266rld\n' > "$TESTS_TMP/p3.txt"
: > "$TESTS_TMP/empty.txt"
printf 'a\tb\vc\fd\r e\n' > "$TESTS_TMP/p5.txt"
{
	index=1
	while ((index <= 9)); do
		printf '%s\n' "$index"
		index=$((index + 1))
	done
} > "$TESTS_TMP/d1.txt"
cp "$TESTS_TMP/d1.txt" "$TESTS_TMP/d2.txt"

counts_suite
options_suite
runner_suite

rm -rf "$TESTS_TMP"
harness_report
