package main

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestStreamQuerySelectAndWhere(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "data.jsonl")
	data := `{"name":"alice","age":30}
{"name":"bob","age":25}
{"name":"carol","age":30}
`
	os.WriteFile(path, []byte(data), 0644)
	f, _ := os.Open(path)
	defer f.Close()
	var buf bytes.Buffer
	err := StreamQuery(f, &buf, Options{Select: []string{"name"}, Where: "age==30"})
	if err != nil {
		t.Fatal(err)
	}
	out := buf.String()
	if !strings.Contains(out, "alice") || !strings.Contains(out, "carol") {
		t.Fatalf("missing expected: %s", out)
	}
	if strings.Contains(out, "bob") {
		t.Fatalf("bob should be filtered: %s", out)
	}
}

func TestStreamQueryCount(t *testing.T) {
	input := `{"x":1}
{"x":2}
{"x":1}
`
	var buf bytes.Buffer
	err := StreamQuery(strings.NewReader(input), &buf, Options{Where: "x==1", Count: true})
	if err != nil {
		t.Fatal(err)
	}
	if strings.TrimSpace(buf.String()) != "2" {
		t.Fatalf("got %q", buf.String())
	}
}

func TestStreamQueryAllFields(t *testing.T) {
	input := `{"a":1,"b":2}
`
	var buf bytes.Buffer
	err := StreamQuery(strings.NewReader(input), &buf, Options{})
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(buf.String(), `"a":1`) {
		t.Fatalf("got %s", buf.String())
	}
}