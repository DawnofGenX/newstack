# shellcheck shell=bash
# tests/counts_test.sh -- the counting core, no files involved.

counts_suite() {
	local data

	textstat_counts_of_data ''
	check 'empty data: lines' "$TEXTSTAT_LINES" 0
	check 'empty data: words' "$TEXTSTAT_WORDS" 0
	check 'empty data: bytes' "$TEXTSTAT_BYTES" 0

	textstat_counts_of_data 'alpha beta'
	check 'no newline: lines' "$TEXTSTAT_LINES" 0
	check 'no newline: words' "$TEXTSTAT_WORDS" 2
	check 'no newline: bytes' "$TEXTSTAT_BYTES" 10

	textstat_counts_of_data 'alpha beta
'
	check 'trailing newline: lines' "$TEXTSTAT_LINES" 1
	check 'trailing newline: words' "$TEXTSTAT_WORDS" 2
	check 'trailing newline: bytes' "$TEXTSTAT_BYTES" 11

	data=$'alpha beta\ngamma delta\n'
	textstat_counts_of_data "$data"
	check 'two lines: lines' "$TEXTSTAT_LINES" 2
	check 'two lines: words' "$TEXTSTAT_WORDS" 4
	check 'two lines: bytes' "$TEXTSTAT_BYTES" 23

	textstat_counts_of_data $'\n\n\n'
	check 'blank lines: lines' "$TEXTSTAT_LINES" 3
	check 'blank lines: words' "$TEXTSTAT_WORDS" 0

	textstat_counts_of_data $'a\tb\vc\fd\r e\n'
	check 'every separator: words' "$TEXTSTAT_WORDS" 5
	check 'every separator: lines' "$TEXTSTAT_LINES" 1

	textstat_counts_of_data $'  leading and trailing  \n'
	check 'padded run: words' "$TEXTSTAT_WORDS" 3

	textstat_counts_of_data $'h\xc3\xa9llo w\xc3\xb6rld\n'
	check 'utf-8 is bytes: bytes' "$TEXTSTAT_BYTES" 14
	check 'utf-8 is bytes: words' "$TEXTSTAT_WORDS" 2
	check 'utf-8 is bytes: lines' "$TEXTSTAT_LINES" 1

	textstat_counts_reset_total
	textstat_counts_add 2 4 23
	textstat_counts_add 0 3 19
	check 'total lines' "$TEXTSTAT_TOTAL_LINES" 2
	check 'total words' "$TEXTSTAT_TOTAL_WORDS" 7
	check 'total bytes' "$TEXTSTAT_TOTAL_BYTES" 42

	check 'columns lwc' "$(textstat_counts_columns 2 4 23 1 1 1)" '2 4 23'
	check 'columns l only' "$(textstat_counts_columns 2 4 23 1 0 0)" '2'
	check 'columns wc' "$(textstat_counts_columns 2 4 23 0 1 1)" '4 23'

	check 'digits of 0' "$(textstat_counts_digits 0)" 1
	check 'digits of 9' "$(textstat_counts_digits 9)" 1
	check 'digits of 10' "$(textstat_counts_digits 10)" 2
	check 'digits of 999' "$(textstat_counts_digits 999)" 3
	check 'digits of 1000' "$(textstat_counts_digits 1000)" 4
}
