package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestDiffBasic(t *testing.T) {
	dir := t.TempDir()
	old := filepath.Join(dir, "old.txt")
	newf := filepath.Join(dir, "new.txt")
	os.WriteFile(old, []byte("a\nb\nc\n"), 0644)
	os.WriteFile(newf, []byte("a\nB\nc\nd\n"), 0644)

	// capture by calling diffLines directly
	o, _ := readLines(old)
	n, _ := readLines(newf)
	out := diffLines(o, n)
	joined := strings.Join(out, "\n")
	if !strings.Contains(joined, "-b") {
		t.Fatalf("missing -b: %s", joined)
	}
	if !strings.Contains(joined, "+B") {
		t.Fatalf("missing +B: %s", joined)
	}
	if !strings.Contains(joined, "+d") {
		t.Fatalf("missing +d: %s", joined)
	}
}
