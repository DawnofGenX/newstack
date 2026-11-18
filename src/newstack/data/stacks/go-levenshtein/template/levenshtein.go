package main

// Distance returns the Levenshtein edit distance between two strings, measured
// in runes so multi byte characters count as one edit each.
func Distance(a, b string) int {
	ra := []rune(a)
	rb := []rune(b)
	if len(ra) == 0 {
		return len(rb)
	}
	if len(rb) == 0 {
		return len(ra)
	}
	prev := make([]int, len(rb)+1)
	curr := make([]int, len(rb)+1)
	for j := 0; j <= len(rb); j++ {
		prev[j] = j
	}
	for i := 1; i <= len(ra); i++ {
		curr[0] = i
		for j := 1; j <= len(rb); j++ {
			cost := 1
			if ra[i-1] == rb[j-1] {
				cost = 0
			}
			best := prev[j] + 1
			if v := curr[j-1] + 1; v < best {
				best = v
			}
			if v := prev[j-1] + cost; v < best {
				best = v
			}
			curr[j] = best
		}
		prev, curr = curr, prev
	}
	return prev[len(rb)]
}

// Closest returns the candidate with the smallest distance, ties broken by order.
func Closest(target string, candidates []string) (string, int, bool) {
	best := ""
	bestDist := 0
	found := false
	for _, candidate := range candidates {
		d := Distance(target, candidate)
		if !found || d < bestDist {
			best = candidate
			bestDist = d
			found = true
		}
	}
	return best, bestDist, found
}
