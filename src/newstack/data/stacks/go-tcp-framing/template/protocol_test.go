package main

import (
	"encoding/json"
	"testing"
)

func decode(t *testing.T, payload string) Reply {
	t.Helper()
	var reply Reply
	encoded, err := Encode(Answer([]byte(payload)))
	if err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal(encoded, &reply); err != nil {
		t.Fatalf("reply is not JSON: %v (%s)", err, encoded)
	}
	return reply
}

func TestCountAnswersWithPointersSoZeroIsVisible(t *testing.T) {
	reply := decode(t, `{"op":"count","text":""}`)
	if !reply.OK || reply.Lines == nil || *reply.Lines != 0 {
		t.Fatalf("a zero count must be printed, got %+v", reply)
	}
	encoded, _ := Encode(reply)
	if string(encoded) != `{"ok":true,"lines":0,"words":0,"bytes":0}` {
		t.Fatalf("wire form %s", encoded)
	}
}

func TestCountCountsBytesNotCharacters(t *testing.T) {
	reply := decode(t, `{"op":"count","text":"h\u00e9llo w\u00f6rld\n"}`)
	if *reply.Bytes != 14 || *reply.Words != 2 || *reply.Lines != 1 {
		t.Fatalf("got %+v", reply)
	}
}

func TestProtocolErrors(t *testing.T) {
	cases := map[string]string{
		`not json`:                "invalid_json",
		`{"text":"a b"}`:          "missing_op",
		`{"op":"nope"}`:           "unknown_op",
		`{"op":"count"}`:          "missing_text",
		`{"op":"count","text":7}`: "invalid_json",
	}
	for payload, want := range cases {
		reply := decode(t, payload)
		if reply.OK || reply.Error != want {
			t.Fatalf("%s: want %s, got %+v", payload, want, reply)
		}
	}
}

func TestCountTextRules(t *testing.T) {
	cases := []struct {
		text  string
		count Counts
	}{
		{"", Counts{0, 0, 0}},
		{"a b", Counts{0, 2, 3}},
		{"a b\n", Counts{1, 2, 4}},
		{" \t\r\n", Counts{1, 0, 4}},
		{"a\x00b", Counts{0, 1, 3}},
		{"\x0b\x0c", Counts{0, 0, 2}},
	}
	for _, test := range cases {
		if got := CountText(test.text); got != test.count {
			t.Fatalf("%q: got %+v want %+v", test.text, got, test.count)
		}
	}
}
