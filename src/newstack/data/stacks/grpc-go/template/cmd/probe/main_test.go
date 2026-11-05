package main

import "testing"

func TestUnescape(t *testing.T) {
	tests := []struct {
		name string
		in   string
		want string
	}{
		{"newline", `a b\nc\n`, "a b\nc\n"},
		{"tab", `a\tb`, "a\tb"},
		{"escaped backslash", `a\\nb`, `a\nb`},
		{"unknown escape is left alone", `50\%%`, `50\%%`},
		{"trailing backslash", `abc\`, `abc\`},
		{"plain text", "hello world", "hello world"},
	}
	for _, test := range tests {
		if got := unescape(test.in); got != test.want {
			t.Errorf("%s: unescape(%q) = %q, want %q", test.name, test.in, got, test.want)
		}
	}
}
