package search

type Match struct {
	Index  int // byte offset in text
	Line   int // 1-based
	Column int // 1-based byte offset within line
}

func Search(text, pattern string) []Match {
	var out []Match
	if pattern == "" {
		return out
	}
	n, m := len(text), len(pattern)
	if m > n {
		return out
	}
	// bad-character skip table
	skip := make([]int, 256)
	for i := range skip {
		skip[i] = m
	}
	for i := 0; i < m-1; i++ {
		skip[pattern[i]] = m - 1 - i
	}
	i := 0
	for i <= n-m {
		j := m - 1
		for j >= 0 && text[i+j] == pattern[j] {
			j--
		}
		if j < 0 {
			out = append(out, location(text, i))
			i++
			continue
		}
		shift := skip[text[i+m-1]]
		if shift < 1 {
			shift = 1
		}
		i += shift
	}
	return out
}

func location(text string, idx int) Match {
	line := 1
	lastNL := -1
	for k := 0; k < idx; k++ {
		if text[k] == '\n' {
			line++
			lastNL = k
		}
	}
	return Match{Index: idx, Line: line, Column: idx - lastNL}
}
