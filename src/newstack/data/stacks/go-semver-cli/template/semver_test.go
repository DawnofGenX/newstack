package main

import "testing"

func TestParseRejectsBadInput(t *testing.T) {
	for _, raw := range []string{"", "1.2", "1.2.3.4", "a.b.c", "1.2.-3", "1.2.3-"} {
		if _, err := Parse(raw); err == nil {
			t.Fatalf("expected error for %q", raw)
		}
	}
}

func TestParseAndString(t *testing.T) {
	v, err := Parse("1.4.2-rc.1+build.7")
	if err != nil {
		t.Fatal(err)
	}
	if v.Major != 1 || v.Minor != 4 || v.Patch != 2 {
		t.Fatalf("unexpected components: %+v", v)
	}
	if v.String() != "1.4.2-rc.1" {
		t.Fatalf("String() = %q", v.String())
	}
}

func TestCompareOrdering(t *testing.T) {
	cases := []struct {
		a, b string
		want int
	}{
		{"1.2.3", "1.2.3", 0},
		{"1.2.3", "1.10.0", -1},
		{"2.0.0", "1.99.99", 1},
		{"1.0.0-alpha", "1.0.0", -1},
		{"1.0.0-alpha", "1.0.0-beta", -1},
		{"1.0.0-alpha.2", "1.0.0-alpha.10", -1},
		{"1.0.0-alpha", "1.0.0-alpha.1", -1},
		{"1.0.0-1", "1.0.0-alpha", -1},
	}
	for _, tc := range cases {
		a, err := Parse(tc.a)
		if err != nil {
			t.Fatal(err)
		}
		b, err := Parse(tc.b)
		if err != nil {
			t.Fatal(err)
		}
		if got := Compare(a, b); got != tc.want {
			t.Fatalf("Compare(%s, %s) = %d, want %d", tc.a, tc.b, got, tc.want)
		}
	}
}

func TestSatisfies(t *testing.T) {
	cases := []struct {
		version    string
		constraint string
		want       bool
	}{
		{"1.9.0", ">=1.2.3", true},
		{"1.2.2", ">=1.2.3", false},
		{"1.2.3", "^1.2.3", true},
		{"2.0.0", "^1.2.3", false},
		{"0.2.9", "^0.2.3", true},
		{"0.3.0", "^0.2.3", false},
		{"1.2.9", "~1.2.3", true},
		{"1.3.0", "~1.2.3", false},
		{"1.2.7", "~1.2", true},
		{"1.2.7", "~1", true},
		{"1.2.7", "1.2.x", true},
		{"1.3.0", "1.2.x", false},
		{"0.9.1", "*", true},
		{"1.2.3", "=1.2.3", true},
		{"1.2.4", "=1.2.3", false},
	}
	for _, tc := range cases {
		v, err := Parse(tc.version)
		if err != nil {
			t.Fatal(err)
		}
		got, err := Satisfies(v, tc.constraint)
		if err != nil {
			t.Fatalf("Satisfies(%s, %s): %v", tc.version, tc.constraint, err)
		}
		if got != tc.want {
			t.Fatalf("Satisfies(%s, %s) = %v, want %v", tc.version, tc.constraint, got, tc.want)
		}
	}
}

func TestSatisfiesRejectsBadConstraint(t *testing.T) {
	v, err := Parse("1.0.0")
	if err != nil {
		t.Fatal(err)
	}
	if _, err := Satisfies(v, ">=nope"); err == nil {
		t.Fatal("expected error for bad constraint")
	}
	if _, err := Satisfies(v, ""); err == nil {
		t.Fatal("expected error for empty constraint")
	}
}
