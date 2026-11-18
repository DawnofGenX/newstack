package main

import "testing"

func TestDistanceKnownValues(t *testing.T) {
	cases := []struct {
		a, b string
		want int
	}{
		{"", "", 0},
		{"", "abc", 3},
		{"abc", "", 3},
		{"same", "same", 0},
		{"kitten", "sitting", 3},
		{"flaw", "lawn", 2},
		{"gumbo", "gambol", 2},
		{"hello", "hello world", 6},
	}
	for _, tc := range cases {
		if got := Distance(tc.a, tc.b); got != tc.want {
			t.Fatalf("Distance(%q, %q) = %d, want %d", tc.a, tc.b, got, tc.want)
		}
	}
}

func TestDistanceIsSymmetric(t *testing.T) {
	pairs := [][2]string{{"abc", "yabd"}, {"kitten", "sitting"}, {"x", ""}}
	for _, p := range pairs {
		if Distance(p[0], p[1]) != Distance(p[1], p[0]) {
			t.Fatalf("asymmetric distance for %v", p)
		}
	}
}

func TestDistanceCountsRunesNotBytes(t *testing.T) {
	if got := Distance("héllo", "hello"); got != 1 {
		t.Fatalf("Distance = %d, want 1", got)
	}
	if got := Distance("日本語", "日本"); got != 1 {
		t.Fatalf("Distance = %d, want 1", got)
	}
}

func TestClosestPicksTheNearest(t *testing.T) {
	// relieve is one substitution away from recieve, while receive needs a
	// transposition, which plain Levenshtein counts as two edits.
	best, dist, ok := Closest("recieve", []string{"receive", "relieve", "believe"})
	if !ok || best != "relieve" || dist != 1 {
		t.Fatalf("Closest = %q %d %v", best, dist, ok)
	}
	if _, d, _ := Closest("recieve", []string{"receive"}); d != 2 {
		t.Fatalf("expected transposition to cost 2, got %d", d)
	}
	if _, _, ok := Closest("x", nil); ok {
		t.Fatal("expected no match for empty candidate list")
	}
}
