# shellcheck shell=bash
# textstat.runner -- turn argv into rows and an exit status.
#
# run() is the whole command: 0 when everything was counted, 1 when a file could
# not be read, 2 when the arguments made no sense. It never exits or prints by
# itself; the io functions decide where that goes, which is how the tests see the
# same output a user does.

# textstat_runner_width_value WIDTH VALUE
#   Print VALUE right-aligned in WIDTH columns.
textstat_runner_width_value() {
	printf '%*d' "$1" "$2"
}

# textstat_runner_width OPERANDS FIGURES REGULAR TOTAL_BYTES
#   Reproduce wc's padding rule, which is not "the widest number you can see":
#   a single figure from a single operand is never padded, an operand of unknown
#   length forces the seven-column default, and otherwise every column is as wide
#   as the total byte count of the operands that were read.
textstat_runner_width() {
	local operands=$1 figures=$2 regular=$3 total_bytes=$4
	if ((operands == 1 && figures == 1)); then
		printf '1'
		return 0
	fi
	if ((regular == 0)); then
		printf '7'
		return 0
	fi
	textstat_counts_digits "$total_bytes"
}

# textstat_runner_run PROGRAM ARGS...
textstat_runner_run() {
	local program=$1
	shift

	textstat_options_parse "$@"

	case $ts_status in
	help)
		local usage
		usage=$(textstat_options_usage "$program")
		textstat_io_out "$usage"$'\n'
		return 0
		;;
	version)
		textstat_io_out "$TEXTSTAT_VERSION"$'\n'
		return 0
		;;
	usage-error)
		textstat_io_err "$program: $ts_message"$'\n'
		textstat_io_err "Try '$program --help' for more information."$'\n'
		return 2
		;;
	esac

	local -a paths=("${ts_files[@]}")
	local implicit=0
	if [[ ${#paths[@]} -eq 0 ]]; then
		paths=("-")
		# wc names the row after the operand it read; with no operand there is
		# nothing to name, so the row carries figures only.
		implicit=1
	fi

	local -a row_columns=() row_labels=()
	local path lines words bytes failed=0 regular=1
	local operands=${#paths[@]}
	textstat_counts_reset_total

	for path in "${paths[@]}"; do
		if [[ $path == - ]]; then
			if ! textstat_io_read_stdin; then
				textstat_io_err "error: cannot open '-'"$'\n'
				failed=1
				continue
			fi
			# A pipe or a terminal has no size to pad against.
			regular=0
		else
			if ! textstat_io_read_file "$path"; then
				textstat_io_err "error: cannot open '$path'"$'\n'
				failed=1
				continue
			fi
			[[ -f $path ]] || regular=0
		fi
		textstat_counts_of_data "$TEXTSTAT_DATA"
		lines=$TEXTSTAT_LINES
		words=$TEXTSTAT_WORDS
		bytes=$TEXTSTAT_BYTES
		textstat_counts_add "$lines" "$words" "$bytes"
		row_columns+=("$(textstat_counts_columns "$lines" "$words" "$bytes" \
			"$ts_show_lines" "$ts_show_words" "$ts_show_bytes")")
		row_labels+=("$path")
	done

	local figures=$((ts_show_lines + ts_show_words + ts_show_bytes))
	local width
	width=$(textstat_runner_width "$operands" "$figures" "$regular" \
		"$TEXTSTAT_TOTAL_BYTES")

	local index cell rendered IFS
	for ((index = 0; index < ${#row_columns[@]}; index++)); do
		rendered=()
		IFS=' '
		for cell in ${row_columns[index]}; do
			rendered+=("$(textstat_runner_width_value "$width" "$cell")")
		done
		if ((implicit)); then
			textstat_io_out "${rendered[*]}"$'\n'
		else
			textstat_io_out "${rendered[*]} ${row_labels[index]}"$'\n'
		fi
	done

	if ((operands > 1)); then
		rendered=()
		IFS=' '
		for cell in $(textstat_counts_columns "$TEXTSTAT_TOTAL_LINES" \
			"$TEXTSTAT_TOTAL_WORDS" "$TEXTSTAT_TOTAL_BYTES" \
			"$ts_show_lines" "$ts_show_words" "$ts_show_bytes"); do
			rendered+=("$(textstat_runner_width_value "$width" "$cell")")
		done
		textstat_io_out "${rendered[*]} total"$'\n'
	fi

	((failed)) && return 1
	return 0
}
