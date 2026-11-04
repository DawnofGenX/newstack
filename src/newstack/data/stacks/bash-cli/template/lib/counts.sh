# shellcheck shell=bash
# textstat.counts -- byte counting over a string, in pure bash.
#
# The counting core never touches the file system: it takes the file's bytes as
# a single string and leaves the figures in TEXTSTAT_LINES / TEXTSTAT_WORDS /
# TEXTSTAT_BYTES, which is what makes it testable without fixtures.

# Bytes that separate words: space, tab, newline, carriage return, vertical tab,
# form feed. Keeping this list explicit is what makes the tool agree with wc.
TEXTSTAT_WHITESPACE=$' \t\n\r\v\f'

# textstat_counts_of_data DATA
#   Count DATA into TEXTSTAT_{LINES,WORDS,BYTES}. Call it with LC_ALL=C set (the
#   entry point and the tests both do) so that ${#data} counts bytes rather than
#   characters.
textstat_counts_of_data() {
	local data=$1
	local newline=$'\n'
	local -a words=()

	TEXTSTAT_BYTES=${#data}
	TEXTSTAT_LINES=0
	TEXTSTAT_WORDS=0

	if [[ $data == *"$newline"* ]]; then
		# Drop everything that is not a newline; what is left is one byte per
		# line. A bash pattern cannot express "not a newline" as an escape, so
		# the newline goes into the bracket expression through a variable.
		local newlines=${data//[!$newline]/}
		TEXTSTAT_LINES=${#newlines}
	fi

	if [[ -n $data ]]; then
		# read -a splits on IFS and drops empty fields, which is exactly the
		# definition of a word here: a maximal run of non-separator bytes.
		IFS=$TEXTSTAT_WHITESPACE read -r -d '' -a words <<< "$data" || :
		TEXTSTAT_WORDS=${#words[@]}
	fi
}

# textstat_counts_add LINES WORDS BYTES
#   Add one row's figures to TEXTSTAT_TOTAL_{LINES,WORDS,BYTES}.
textstat_counts_add() {
	TEXTSTAT_TOTAL_LINES=$((TEXTSTAT_TOTAL_LINES + $1))
	TEXTSTAT_TOTAL_WORDS=$((TEXTSTAT_TOTAL_WORDS + $2))
	TEXTSTAT_TOTAL_BYTES=$((TEXTSTAT_TOTAL_BYTES + $3))
}

# textstat_counts_reset_total
textstat_counts_reset_total() {
	TEXTSTAT_TOTAL_LINES=0
	TEXTSTAT_TOTAL_WORDS=0
	TEXTSTAT_TOTAL_BYTES=0
}

# textstat_counts_columns LINES WORDS BYTES SHOW_LINES SHOW_WORDS SHOW_BYTES
#   Print the requested figures in wc's canonical order, separated by a space,
#   with no trailing space.
textstat_counts_columns() {
	local out=()
	(( $4 )) && out+=("$1")
	(( $5 )) && out+=("$2")
	(( $6 )) && out+=("$3")
	local IFS=' '
	printf '%s' "${out[*]}"
}

# textstat_counts_digits VALUE
#   Echo the number of decimal digits in a non-negative integer.
textstat_counts_digits() {
	local value=$1 digits=1
	while (( value >= 10 )); do
		value=$((value / 10))
		digits=$((digits + 1))
	done
	printf '%s' "$digits"
}
