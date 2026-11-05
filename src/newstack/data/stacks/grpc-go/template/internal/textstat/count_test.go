package textstat

import "testing"

func TestCount(t *testing.T) {
	tests := []struct {
		name string
		text string
		want Counts
	}{
		{name: "one line", text: "hello world\n", want: Counts{Lines: 1, Words: 2, Bytes: 12}},
		{name: "two lines", text: "a b\nc\n", want: Counts{Lines: 2, Words: 3, Bytes: 6}},
		{name: "empty", text: "", want: Counts{Lines: 0, Words: 0, Bytes: 0}},
		{name: "whitespace only", text: "  \t ", want: Counts{Lines: 0, Words: 0, Bytes: 4}},
		{name: "no trailing newline", text: "abc", want: Counts{Lines: 0, Words: 1, Bytes: 3}},
		{name: "utf8 bytes not characters", text: "héllo wörld\n", want: Counts{Lines: 1, Words: 2, Bytes: 14}},
		{name: "emoji", text: "🙂\n", want: Counts{Lines: 1, Words: 1, Bytes: 5}},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := Count(tt.text); got != tt.want {
				t.Errorf("Count(%q) = %+v, want %+v", tt.text, got, tt.want)
			}
		})
	}
}

func TestValidUTF8(t *testing.T) {
	if !ValidUTF8("héllo") {
		t.Error("valid UTF-8 reported as invalid")
	}
	if ValidUTF8("\xff\xfe") {
		t.Error("invalid UTF-8 reported as valid")
	}
}
