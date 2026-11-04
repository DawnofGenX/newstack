# shellcheck shell=bash
# textstat.options -- hand-rolled argv parsing.
#
# parse leaves its answer in the TS_* globals rather than returning a record,
# because a bash function can only return an exit status. Every other module
# reads those globals and never looks at "$@" again.

TEXTSTAT_VERSION='0.1.0'

ts_status=ok
ts_message=
ts_files=()
ts_show_lines=0
ts_show_words=0
ts_show_bytes=0
ts_any_figure=0

# textstat_options_reset
textstat_options_reset() {
	ts_status=ok
	ts_message=
	ts_files=()
	ts_show_lines=0
	ts_show_words=0
	ts_show_bytes=0
	ts_any_figure=0
}

# textstat_options_usage PROGRAM
textstat_options_usage() {
	local program=$1
	printf 'Usage: %s [OPTION]... [FILE]...\n' "$program"
	printf 'Count lines, words, and bytes in each FILE.\n'
	printf 'With no FILE, or when FILE is -, read standard input.\n'
	printf '\n'
	printf '  -l, --lines    print the line count\n'
	printf '  -w, --words    print the word count\n'
	printf '  -c, --bytes    print the byte count\n'
	printf '  -h, --help     show this help and exit\n'
	printf '  -V, --version  show the version and exit\n'
}

# textstat_options_figure LETTER
#   -- set one figure flag; l, w and c are the only letters that reach here.
textstat_options_figure() {
	case $1 in
	l) ts_show_lines=1 ;;
	w) ts_show_words=1 ;;
	c) ts_show_bytes=1 ;;
	esac
	ts_any_figure=1
}

# textstat_options_cluster LETTERS
#   -- walk a short-flag cluster such as -lw. Returns 1 when the cluster has
#   already decided the outcome (help, version, or a usage error).
textstat_options_cluster() {
	local letters=$1 index letter
	for ((index = 0; index < ${#letters}; index++)); do
		letter=${letters:index:1}
		case $letter in
		l | w | c)
			textstat_options_figure "$letter"
			;;
		h)
			ts_status=help
			return 1
			;;
		V)
			ts_status=version
			return 1
			;;
		*)
			ts_status=usage-error
			ts_message="unknown option: -$letter"
			return 1
			;;
		esac
	done
	return 0
}

# textstat_options_parse ARGS...
textstat_options_parse() {
	local literal=0 argument
	textstat_options_reset

	while (( $# > 0 )); do
		argument=$1
		shift
		if (( literal )); then
			ts_files+=("$argument")
			continue
		fi
		case $argument in
		--)
			literal=1
			;;
		--lines) textstat_options_figure l ;;
		--words) textstat_options_figure w ;;
		--bytes) textstat_options_figure c ;;
		--help)
			ts_status=help
			return 0
			;;
		--version)
			ts_status=version
			return 0
			;;
		-)
			ts_files+=("-")
			;;
		--*)
			ts_status=usage-error
			ts_message="unknown option: $argument"
			return 0
			;;
		-*)
			textstat_options_cluster "${argument#-}" || return 0
			;;
		*)
			ts_files+=("$argument")
			;;
		esac
	done

	if ((ts_any_figure == 0)); then
		ts_show_lines=1
		ts_show_words=1
		ts_show_bytes=1
	fi
	return 0
}
