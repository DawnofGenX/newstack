# shellcheck shell=bash
# textstat.io -- the only module that touches the real process.
#
# The runner calls these four functions and nothing else, so a test swaps them
# for versions that read fixed strings and append to buffers.

# textstat_io_out TEXT -- write TEXT to standard output.
textstat_io_out() {
	printf '%s' "$1"
}

# textstat_io_err TEXT -- write TEXT to standard error.
textstat_io_err() {
	printf '%s' "$1" >&2
}

# textstat_io_read_file PATH
#   Read PATH byte-exactly into TEXTSTAT_DATA. Returns 1 when PATH cannot be
#   read. A trailing newline survives the round trip because a sentinel byte is
#   appended before the command substitution strips anything, and removed after.
textstat_io_read_file() {
	local path=$1 body
	if [[ ! -f $path || ! -r $path ]]; then
		return 1
	fi
	body=$(cat -- "$path" && printf 'x') || return 1
	TEXTSTAT_DATA=${body%x}
	return 0
}

# textstat_io_read_stdin -- read standard input byte-exactly into TEXTSTAT_DATA.
textstat_io_read_stdin() {
	local body
	body=$(cat && printf 'x') || return 1
	TEXTSTAT_DATA=${body%x}
	return 0
}
