// Package textstat counts text the way `wc` does, with no transport in sight, so the rules
// can be tested as plain Go before any gRPC is involved.
package textstat

import (
	"strings"
	"unicode/utf8"
)

// Counts are the three numbers both `wc` and this service report.
type Counts struct {
	Lines int64
	Words int64
	Bytes int64
}

// Count measures text. A line is a newline character, a word is a maximal run of
// non-whitespace, and Bytes is the length in bytes — len() on a Go string is already bytes,
// so a multi-byte character counts once per byte and never as one "character".
func Count(text string) Counts {
	return Counts{
		Lines: int64(strings.Count(text, "\n")),
		Words: int64(len(strings.Fields(text))),
		Bytes: int64(len(text)),
	}
}

// ValidUTF8 reports whether text is valid UTF-8, which is the one precondition the wire
// format cannot express (protobuf strings are bytes on the wire).
func ValidUTF8(text string) bool {
	return utf8.ValidString(text)
}
