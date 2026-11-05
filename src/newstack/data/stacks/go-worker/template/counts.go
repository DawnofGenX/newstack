package main

// Counts is what a "count" job reports: the same numbers `wc` gives, measured
// over the UTF-8 bytes rather than the runes.
type Counts struct {
	Lines int `json:"lines"`
	Words int `json:"words"`
	Bytes int `json:"bytes"`
}

func countText(text string) Counts {
	raw := []byte(text)
	counts := Counts{Bytes: len(raw)}
	inWord := false
	for _, b := range raw {
		if b == '\n' {
			counts.Lines++
		}
		if isSeparator(b) {
			inWord = false
			continue
		}
		if !inWord {
			inWord = true
			counts.Words++
		}
	}
	return counts
}

func isSeparator(b byte) bool {
	switch b {
	case ' ', '\t', '\n', '\r', 0x0b, 0x0c:
		return true
	}
	return false
}
