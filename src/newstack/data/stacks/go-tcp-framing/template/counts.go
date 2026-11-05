package main

// Counts is the answer every count request carries.
type Counts struct {
	Lines int
	Words int
	Bytes int
}

func isSeparator(b byte) bool {
	switch b {
	case ' ', '\t', '\n', '\r', 0x0b, 0x0c:
		return true
	default:
		return false
	}
}

// CountText counts raw UTF-8 bytes: a word starts only after a separator, and
// "héllo wörld\n" is 14 bytes while it is 12 characters.
func CountText(text string) Counts {
	inside := false
	counts := Counts{Bytes: len(text)}
	for i := 0; i < len(text); i++ {
		if text[i] == '\n' {
			counts.Lines++
		}
		if isSeparator(text[i]) {
			inside = false
		} else if !inside {
			inside = true
			counts.Words++
		}
	}
	return counts
}
