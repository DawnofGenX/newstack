package main

import (
	"bytes"
	"encoding/binary"
	"errors"
	"strings"
	"testing"
)

func TestFrameRoundTrip(t *testing.T) {
	buffer := &bytes.Buffer{}
	if err := WriteFrame(buffer, []byte(`{"op":"ping"}`)); err != nil {
		t.Fatal(err)
	}
	if got := len(buffer.Bytes()); got != 4+13 {
		t.Fatalf("wrote %d bytes, want 17", got)
	}
	if size := binary.BigEndian.Uint32(buffer.Bytes()[:4]); size != 13 {
		t.Fatalf("header says %d, want 13", size)
	}
	payload, err := ReadFrame(buffer, MaxFrame)
	if err != nil {
		t.Fatal(err)
	}
	if string(payload) != `{"op":"ping"}` {
		t.Fatalf("payload %q", payload)
	}
}

func TestReadFrameRefusesAnEmptyOrOversizedHeader(t *testing.T) {
	empty := bytes.NewReader([]byte{0, 0, 0, 0})
	if _, err := ReadFrame(empty, MaxFrame); !errors.Is(err, ErrEmptyFrame) {
		t.Fatalf("want ErrEmptyFrame, got %v", err)
	}

	head := make([]byte, 4)
	binary.BigEndian.PutUint32(head, MaxFrame+1)
	if _, err := ReadFrame(bytes.NewReader(head), MaxFrame); !errors.Is(err, ErrFrameTooLarge) {
		t.Fatalf("want ErrFrameTooLarge, got %v", err)
	}
}

func TestReadFrameRefusesATruncatedBody(t *testing.T) {
	frame := []byte{0, 0, 0, 10, 'a', 'b'}
	if _, err := ReadFrame(bytes.NewReader(frame), MaxFrame); err == nil {
		t.Fatal("a body shorter than its header must not be accepted")
	}
}

func TestWriteFrameRefusesTooMuch(t *testing.T) {
	if err := WriteFrame(&bytes.Buffer{}, nil); !errors.Is(err, ErrEmptyFrame) {
		t.Fatalf("want ErrEmptyFrame, got %v", err)
	}
	huge := strings.Repeat("x", MaxFrame+1)
	if err := WriteFrame(&bytes.Buffer{}, []byte(huge)); !errors.Is(err, ErrFrameTooLarge) {
		t.Fatalf("want ErrFrameTooLarge, got %v", err)
	}
}
