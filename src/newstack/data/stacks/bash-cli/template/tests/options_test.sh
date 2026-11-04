# shellcheck shell=bash
# tests/options_test.sh -- argv parsing, observed through the ts_* globals.

options_suite() {
	textstat_options_parse
	check 'no arguments: status' "$ts_status" ok
	check 'no arguments: file count' "${#ts_files[@]}" 0
	check 'no arguments: every figure' "$ts_show_lines$ts_show_words$ts_show_bytes" 111

	textstat_options_parse -l
	check '-l: lines' "$ts_show_lines" 1
	check '-l: words' "$ts_show_words" 0
	check '-l: bytes' "$ts_show_bytes" 0

	textstat_options_parse --bytes
	check '--bytes: bytes' "$ts_show_bytes" 1
	check '--bytes: lines' "$ts_show_lines" 0

	textstat_options_parse -lw
	check 'cluster -lw: lines' "$ts_show_lines" 1
	check 'cluster -lw: words' "$ts_show_words" 1
	check 'cluster -lw: bytes' "$ts_show_bytes" 0

	textstat_options_parse -l -l --lines
	check 'repeated figure: lines' "$ts_show_lines" 1

	textstat_options_parse --help
	check '--help: status' "$ts_status" help
	textstat_options_parse -h
	check '-h: status' "$ts_status" help

	textstat_options_parse --version
	check '--version: status' "$ts_status" version
	textstat_options_parse -V
	check '-V: status' "$ts_status" version

	textstat_options_parse --bogus
	check '--bogus: status' "$ts_status" usage-error
	check '--bogus: message' "$ts_message" 'unknown option: --bogus'

	textstat_options_parse -x
	check '-x: status' "$ts_status" usage-error
	check '-x: message' "$ts_message" 'unknown option: -x'

	textstat_options_parse -lwq
	check 'cluster with an unknown letter: status' "$ts_status" usage-error
	check 'cluster with an unknown letter: message' "$ts_message" 'unknown option: -q'

	textstat_options_parse a.txt b.txt
	check 'two files: count' "${#ts_files[@]}" 2
	check 'two files: first' "${ts_files[0]}" a.txt
	check 'two files: second' "${ts_files[1]}" b.txt
	check 'two files: default figures' "$ts_show_lines$ts_show_words$ts_show_bytes" 111

	textstat_options_parse -- -l
	check '-- makes -l a file' "${ts_files[0]}" '-l'
	check '-- keeps the default figures' "$ts_show_lines$ts_show_words$ts_show_bytes" 111

	textstat_options_parse -
	check 'a lone dash is a file' "${ts_files[0]}" '-'

	textstat_options_parse -l -- -w
	check 'figure before -- still applies' "$ts_show_lines" 1
	check '-- -w is a file' "${ts_files[0]}" '-w'

	local usage
	usage=$(textstat_options_usage sample)
	check 'usage names the program' \
		"$([[ $usage == *'Usage: sample [OPTION]... [FILE]...'* ]] && echo yes)" yes
	check 'usage documents every figure' \
		"$([[ $usage == *'--lines'* && $usage == *'--words'* && $usage == *'--bytes'* ]] && echo yes)" yes

	check 'version string' "$TEXTSTAT_VERSION" '0.1.0'
}
