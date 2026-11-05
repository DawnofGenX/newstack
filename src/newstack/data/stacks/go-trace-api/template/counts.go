package main

// Counts is the text statistic every response carries.
type Counts struct {
	Lines int `json:"lines"`
	Words int `json:"words"`
	Bytes int `json:"bytes"`
}

func isSeparator(b byte) bool {
	switch b {
	case 0x20, 0x09, 0x0A, 0x0D, 0x0B, 0x0C:
		return true
	}
	return false
}

// CountText counts over UTF-8 bytes: runes are irrelevant, bytes are what a
// Content-Length talks about.
func CountText(text string) Counts {
	data := []byte(text)
	counts := Counts{Bytes: len(data)}
	inWord := false
	for _, b := range data {
		if b == 0x0A {
			counts.Lines++
		}
		if isSeparator(b) {
			inWord = false
			continue
		}
		if !inWord {
			counts.Words++
			inWord = true
		}
	}
	return counts
}
