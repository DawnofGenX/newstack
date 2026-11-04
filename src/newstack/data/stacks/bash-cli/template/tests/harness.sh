# shellcheck shell=bash
# tests/harness.sh -- assertion helpers and a fake terminal.
#
# The runner writes through the io functions, so a test swaps the two writers for
# buffers and reads back exactly what the user would see. Reading stays real: the
# suites write fixture files and let lib/io.sh read them.

# shellcheck source=../lib/io.sh
. "$TESTS_ROOT/lib/io.sh"

TEXTSTAT_TESTS_PASSED=0
TEXTSTAT_TESTS_FAILED=0
OUT_BUF=
ERR_BUF=

# Standard input is not a pipe here: the suites set HARNESS_STDIN instead, and
# the shipped `stdin` check in stack.json is what exercises the real thing.
HARNESS_STDIN=

# shellcheck disable=SC2317
textstat_io_read_stdin() { TEXTSTAT_DATA=$HARNESS_STDIN; }

# textstat_io_out / textstat_io_err -- capture instead of printing.
# shellcheck disable=SC2317  # called by lib/runner.sh, not from this file
textstat_io_out() { OUT_BUF+=$1; }
# shellcheck disable=SC2317
textstat_io_err() { ERR_BUF+=$1; }

harness_reset() {
	OUT_BUF=
	ERR_BUF=
}

# check NAME ACTUAL EXPECTED
check() {
	local name=$1 actual=$2 expected=$3
	if [[ $actual == "$expected" ]]; then
		TEXTSTAT_TESTS_PASSED=$((TEXTSTAT_TESTS_PASSED + 1))
	else
		TEXTSTAT_TESTS_FAILED=$((TEXTSTAT_TESTS_FAILED + 1))
		printf 'FAIL %s\n  actual:   [%s]\n  expected: [%s]\n' \
			"$name" "$actual" "$expected"
	fi
}

# check_not_empty NAME ACTUAL
check_not_empty() {
	local name=$1 actual=$2
	if [[ -n $actual ]]; then
		TEXTSTAT_TESTS_PASSED=$((TEXTSTAT_TESTS_PASSED + 1))
	else
		TEXTSTAT_TESTS_FAILED=$((TEXTSTAT_TESTS_FAILED + 1))
		printf 'FAIL %s\n  expected something, got nothing\n' "$name"
	fi
}

# check_file NAME PATH
check_file() {
	check "$1 exists" "$([[ -f $2 ]] && echo yes)" yes
}

# harness_report -- print the tally and return 1 when anything failed.
harness_report() {
	local total=$((TEXTSTAT_TESTS_PASSED + TEXTSTAT_TESTS_FAILED))
	printf 'checks: %d, passed: %d, failed: %d\n' \
		"$total" "$TEXTSTAT_TESTS_PASSED" "$TEXTSTAT_TESTS_FAILED"
	((TEXTSTAT_TESTS_FAILED == 0)) || return 1
	return 0
}
