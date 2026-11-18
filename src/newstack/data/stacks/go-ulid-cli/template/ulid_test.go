package main

import (
	"strings"
	"testing"
	"time"
)

func fixedEntropy(b byte) [10]byte {
	var e [10]byte
	for i := range e {
		e[i] = b
	}
	return e
}

func TestNewHasFixedLengthAndAlphabet(t *testing.T) {
	at := time.UnixMilli(1_700_000_000_123).UTC()
	id := NewFrom(at, fixedEntropy(0x2A))
	if len(id) != 26 {
		t.Fatalf("len = %d, want 26", len(id))
	}
	for i := 0; i < len(id); i++ {
		if !strings.ContainsRune(crockford, rune(id[i])) {
			t.Fatalf("unexpected char %q", id[i])
		}
	}
	if id[0] > '7' {
		t.Fatalf("first char %q overflows 128 bits", id[0])
	}
	if strings.ContainsAny(id, "ILOU") {
		t.Fatalf("id contains excluded letters: %s", id)
	}
}

func TestTimestampRoundtrip(t *testing.T) {
	at := time.UnixMilli(1_700_000_000_123).UTC()
	id := NewFrom(at, fixedEntropy(1))
	got, err := Timestamp(id)
	if err != nil {
		t.Fatal(err)
	}
	if !got.Equal(at) {
		t.Fatalf("timestamp = %s, want %s", got, at)
	}
}

func TestLaterTimestampsSortHigher(t *testing.T) {
	base := time.UnixMilli(1_700_000_000_000).UTC()
	early := NewFrom(base, fixedEntropy(9))
	late := NewFrom(base.Add(5*time.Second), fixedEntropy(0))
	if !(early < late) {
		t.Fatalf("expected %s < %s", early, late)
	}
}

func TestParseRejectsBadInput(t *testing.T) {
	if _, err := Timestamp("short"); err == nil {
		t.Fatal("expected length error")
	}
	if _, err := Timestamp("0000000000000000000000000I"); err == nil {
		t.Fatal("expected alphabet error for I")
	}
	if _, err := Timestamp("0000000000000000000000000U"); err == nil {
		t.Fatal("expected alphabet error for U")
	}
}

func TestNewProducesDistinctIds(t *testing.T) {
	at := time.UnixMilli(1_700_000_000_000).UTC()
	seen := map[string]bool{}
	for i := 0; i < 50; i++ {
		id, err := New(at)
		if err != nil {
			t.Fatal(err)
		}
		if seen[id] {
			t.Fatalf("duplicate id %s", id)
		}
		seen[id] = true
	}
}
