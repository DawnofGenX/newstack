package main

import (
	"archive/tar"
	"bytes"
	"compress/gzip"
	"os"
	"path/filepath"
	"testing"
)

func makeArchive(t *testing.T, entries []struct{ name, content string }) *bytes.Buffer {
	t.Helper()
	var buf bytes.Buffer
	gz := gzip.NewWriter(&buf)
	tw := tar.NewWriter(gz)
	for _, e := range entries {
		hdr := &tar.Header{Name: e.name, Mode: 0644, Size: int64(len(e.content)), Typeflag: tar.TypeReg}
		tw.WriteHeader(hdr)
		tw.Write([]byte(e.content))
	}
	tw.Close()
	gz.Close()
	return &buf
}

func TestGoodArchive(t *testing.T) {
	buf := makeArchive(t, []struct{ name, content string }{{"hello.txt", "hi"}})
	dir := t.TempDir()
	if err := ExtractArchive(bytes.NewReader(buf.Bytes()), dir); err != nil {
		t.Fatal(err)
	}
	b, err := os.ReadFile(filepath.Join(dir, "hello.txt"))
	if err != nil || string(b) != "hi" {
		t.Fatalf("got %s %v", b, err)
	}
}

func TestRejectsPathTraversal(t *testing.T) {
	// manually create archive with ../evil.txt
	var buf bytes.Buffer
	gz := gzip.NewWriter(&buf)
	tw := tar.NewWriter(gz)
	hdr := &tar.Header{Name: "../evil.txt", Mode: 0644, Size: 4, Typeflag: tar.TypeReg}
	tw.WriteHeader(hdr)
	tw.Write([]byte("evil"))
	tw.Close()
	gz.Close()
	dir := t.TempDir()
	if err := ExtractArchive(bytes.NewReader(buf.Bytes()), dir); err == nil {
		t.Fatal("expected error")
	}
}

func TestRejectsAbsolutePath(t *testing.T) {
	var buf bytes.Buffer
	gz := gzip.NewWriter(&buf)
	tw := tar.NewWriter(gz)
	hdr := &tar.Header{Name: "/etc/passwd", Mode: 0644, Size: 4, Typeflag: tar.TypeReg}
	tw.WriteHeader(hdr)
	tw.Write([]byte("evil"))
	tw.Close()
	gz.Close()
	dir := t.TempDir()
	if err := ExtractArchive(bytes.NewReader(buf.Bytes()), dir); err == nil {
		t.Fatal("expected error")
	}
}