package main

import "testing"

func TestParseTraceparentAcceptsAValidHeader(t *testing.T) {
	const header = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
	parsed, err := ParseTraceparent(header)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if parsed.TraceID != "4bf92f3577b34da6a3ce929d0e0e4736" || parsed.SpanID != "00f067aa0ba902b7" {
		t.Fatalf("ids not preserved: %+v", parsed)
	}
	if !parsed.Sampled() {
		t.Fatal("flags 01 must mean sampled")
	}
	if parsed.String() != header {
		t.Fatalf("round trip changed the header: %s", parsed.String())
	}
}

func TestParseTraceparentRejectsMalformedHeaders(t *testing.T) {
	for name, header := range map[string]string{
		"empty":         "",
		"three fields":  "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7",
		"uppercase":     "00-4BF92F3577B34DA6A3CE929D0E0E4736-00f067aa0ba902b7-01",
		"zero trace":    "00-00000000000000000000000000000000-00f067aa0ba902b7-01",
		"zero span":     "00-4bf92f3577b34da6a3ce929d0e0e4736-0000000000000000-01",
		"bad version":   "ff-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
		"bad flags":     "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-0z",
		"short trace":   "00-4bf92f-00f067aa0ba902b7-01",
		"extra garbage": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01-99",
	} {
		if _, err := ParseTraceparent(header); err == nil {
			t.Fatalf("%s: expected an error", name)
		}
	}
}

func TestChildKeepsTheTraceAndMintsASpan(t *testing.T) {
	parent, err := ParseTraceparent("00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-00")
	if err != nil {
		t.Fatal(err)
	}
	child := parent.Child()
	if child.TraceID != parent.TraceID {
		t.Fatal("the trace id must survive")
	}
	if child.SpanID == parent.SpanID {
		t.Fatal("the span id must be new")
	}
	if child.Sampled() {
		t.Fatal("the flags must survive")
	}
}

func TestCountTextCountsUtf8Bytes(t *testing.T) {
	counts := CountText("h\u00e9llo w\u00f6rld\n")
	if counts.Lines != 1 || counts.Words != 2 || counts.Bytes != 14 {
		t.Fatalf("got %+v, want 1/2/14", counts)
	}
}
