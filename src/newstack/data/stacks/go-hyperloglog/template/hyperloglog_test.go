package main

import (
	"fmt"
	"strings"
	"testing"
)

func TestHyperLogLogBasic(t *testing.T) {
	var b strings.Builder
	for i := 0; i < 1000; i++ {
		fmt.Fprintf(&b, "item%d\n", i)
	}
	est, err := run(strings.NewReader(b.String()), 12)
	if err != nil {
		t.Fatal(err)
	}
	if est < 800 || est > 1200 {
		t.Fatalf("estimate %.0f out of range", est)
	}
}

func TestHyperLogLogEmpty(t *testing.T) {
	est, err := run(strings.NewReader(""), 12)
	if err != nil {
		t.Fatal(err)
	}
	if est != 0 {
		t.Fatalf("got %.0f", est)
	}
}
