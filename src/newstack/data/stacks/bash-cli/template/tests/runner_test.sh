# shellcheck shell=bash
# tests/runner_test.sh -- the whole command, driven through the fake terminal.
#
# Fixtures live in TESTS_TMP (created by run_tests.sh). The only swappable input
# is standard input: HARNESS_STDIN stands in for a pipe.

runner_suite() {
	local tmp=$TESTS_TMP status

	# One file, every figure.
	harness_reset
	textstat_runner_run sample "$tmp/p1.txt"
	status=$?
	check 'one file: exit status' "$status" 0
	check 'one file: row' "$OUT_BUF" " 2  4 23 $tmp/p1.txt"$'\n'
	check 'one file: nothing on stderr' "$ERR_BUF" ''

	# A figure subset keeps wc's canonical order whatever the flag order is.
	harness_reset
	textstat_runner_run sample -c -l "$tmp/p1.txt"
	check 'reordered flags: canonical order' "$OUT_BUF" " 2 23 $tmp/p1.txt"$'\n'

	# The columns are as wide as the total byte count, not as wide as the widest
	# number being printed: p1.txt is 23 bytes, so -l -w pads to two columns even
	# though 2 and 4 are one digit each.
	harness_reset
	textstat_runner_run sample -l -w "$tmp/p1.txt"
	check 'width comes from the byte count' "$OUT_BUF" " 2  4 $tmp/p1.txt"$'\n'

	harness_reset
	textstat_runner_run sample -l "$tmp/p1.txt"
	check 'single figure: row' "$OUT_BUF" "2 $tmp/p1.txt"$'\n'

	# Two files get a total row, and the width grows to fit it.
	harness_reset
	textstat_runner_run sample "$tmp/d1.txt" "$tmp/d2.txt"
	check 'two files: first row' "${OUT_BUF%%$'\n'*}" " 9  9 18 $tmp/d1.txt"
	check 'two files: total row' "$(printf '%s' "${OUT_BUF%$'\n'}" | tail -1)" '18 18 36 total'

	# Standard input: implicit, and as an explicit dash.
	HARNESS_STDIN=$'alpha beta\ngamma\n'
	harness_reset
	textstat_runner_run sample
	check 'no operand: reads stdin' "$OUT_BUF" '      2       3      17'$'\n'

	harness_reset
	textstat_runner_run sample -w -
	# One figure from one operand is never padded, even when the operand is a pipe.
	check 'dash operand: reads stdin' "$OUT_BUF" '3 -'$'\n'

	# A missing file is reported, printed nowhere, and still counted for the
	# total when another operand was read.
	harness_reset
	textstat_runner_run sample "$tmp/p1.txt" "$tmp/absent.txt"
	status=$?
	check 'missing file: exit status' "$status" 1
	check 'missing file: message' "$ERR_BUF" "error: cannot open '$tmp/absent.txt'"$'\n'
	check 'missing file: row' "$OUT_BUF" " 2  4 23 $tmp/p1.txt"$'\n 2  4 23 total'$'\n'

	harness_reset
	textstat_runner_run sample "$tmp/absent.txt"
	status=$?
	check 'only a missing file: exit status' "$status" 1
	check 'only a missing file: no rows' "$OUT_BUF" ''
	check 'only a missing file: message' \
		"$ERR_BUF" "error: cannot open '$tmp/absent.txt'"$'\n'

	# Help and version go to standard output and succeed.
	harness_reset
	textstat_runner_run sample --help
	status=$?
	check '--help: exit status' "$status" 0
	check_not_empty '--help: writes usage' "$OUT_BUF"

	harness_reset
	textstat_runner_run sample --version
	status=$?
	check '--version: exit status' "$status" 0
	check '--version: output' "$OUT_BUF" '0.1.0'$'\n'

	# A bad argument is a usage error: two lines on stderr, nothing on stdout.
	harness_reset
	textstat_runner_run sample --bogus
	status=$?
	check '--bogus: exit status' "$status" 2
	check '--bogus: nothing on stdout' "$OUT_BUF" ''
	check '--bogus: stderr' "$ERR_BUF" \
		"sample: unknown option: --bogus"$'\n'"Try 'sample --help' for more information."$'\n'

	# The padding rule itself.
	check 'width: one operand, one figure' "$(textstat_runner_width 1 1 1 23)" 1
	check 'width: one operand, two figures' "$(textstat_runner_width 1 2 1 23)" 2
	check 'width: three-digit total' "$(textstat_runner_width 2 2 1 102)" 3
	check 'width: empty files' "$(textstat_runner_width 2 3 1 0)" 1
	check 'width: a stream' "$(textstat_runner_width 3 3 0 999)" 7

	# An empty file is three zeroes, not a blank line.
	harness_reset
	textstat_runner_run sample "$tmp/empty.txt"
	check 'empty file: row' "$OUT_BUF" "0 0 0 $tmp/empty.txt"$'\n'
}
