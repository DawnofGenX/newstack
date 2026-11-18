package main

import (
	"bytes"
	"encoding/hex"
	"strings"
	"testing"
)

func fromHex(t *testing.T, text string) []byte {
	t.Helper()
	out, err := hex.DecodeString(text)
	if err != nil {
		t.Fatalf("bad test vector: %v", err)
	}
	return out
}

// RFC 5869 appendix A.1: SHA-256, salt 13 bytes, info 10 bytes, L = 42.
func TestRFC5869Case1(t *testing.T) {
	ikm := fromHex(t, strings.Repeat("0b", 22))
	salt := fromHex(t, "000102030405060708090a0b0c")
	info := fromHex(t, "f0f1f2f3f4f5f6f7f8f9")
	want := "3cb25f25faacd57a90434f64d0362f2a2d2d0a90cf1a5a4c5db02d56ecc4c5bf34007208d5b887185865"

	got, err := Derive(salt, ikm, info, 42)
	if err != nil {
		t.Fatalf("Derive: %v", err)
	}
	if hex.EncodeToString(got) != want {
		t.Fatalf("got %x want %s", got, want)
	}
}

// RFC 5869 appendix A.3: zero-length salt and info.
func TestRFC5869Case3(t *testing.T) {
	ikm := fromHex(t, strings.Repeat("0b", 22))
	want := "8da4e775a563c18f715f802a063c5a31b8a11f5c5ee1879ec3454e5f3c738d2d9d201395faa4b61a96c8"

	got, err := Derive(nil, ikm, nil, 42)
	if err != nil {
		t.Fatalf("Derive: %v", err)
	}
	if hex.EncodeToString(got) != want {
		t.Fatalf("got %x want %s", got, want)
	}
}

func TestExpandRejectsBadLength(t *testing.T) {
	if _, err := Expand(make([]byte, HashLen), nil, 0); err == nil {
		t.Fatal("length 0 should be refused")
	}
	if _, err := Expand(make([]byte, HashLen), nil, 8161); err == nil {
		t.Fatal("length past 255 blocks should be refused")
	}
}

func TestExpandIsAPrefix(t *testing.T) {
	prk := Extract([]byte("salt"), []byte("input"))
	long, err := Expand(prk, []byte("info"), 64)
	if err != nil {
		t.Fatalf("Expand: %v", err)
	}
	short, err := Expand(prk, []byte("info"), 32)
	if err != nil {
		t.Fatalf("Expand: %v", err)
	}
	if !bytes.Equal(long[:32], short) {
		t.Fatal("a shorter output must be a prefix of a longer one")
	}
	if bytes.Equal(long[:32], long[32:]) {
		t.Fatal("consecutive blocks must differ")
	}
}

func TestCLIHexVector(t *testing.T) {
	out, err := run([]string{"-salt", "000102030405060708090a0b0c", "-info", "\u00e5", "-length", "4", strings.Repeat("0b", 22)}, nil)
	if err != nil {
		t.Fatalf("run: %v", err)
	}
	if len(out) != 8 {
		t.Fatalf("expected 8 hex digits, got %q", out)
	}
}

func TestCLIReadsStdin(t *testing.T) {
	out, err := run([]string{"-length", "16"}, []byte("key material"))
	if err != nil {
		t.Fatalf("run: %v", err)
	}
	if len(out) != 32 {
		t.Fatalf("expected 32 hex digits, got %q", out)
	}
}

func TestCLIRejectsOddHex(t *testing.T) {
	if _, err := run([]string{"abc"}, nil); err == nil {
		t.Fatal("odd length hex should be refused")
	}
}

func TestCLIRejectsUnknownOption(t *testing.T) {
	if _, err := run([]string{"--bogus"}, nil); err == nil {
		t.Fatal("an unknown option should be refused")
	}
}
