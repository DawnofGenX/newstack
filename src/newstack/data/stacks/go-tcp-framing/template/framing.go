package main

import (
	"encoding/binary"
	"errors"
	"fmt"
	"io"
)

// MaxFrame is the largest payload one frame may carry. Anything bigger is
// refused before a buffer is allocated for it: a length prefix is an
// allocation instruction from the network, and a 4 GiB "message" is one
// handshake away.
const MaxFrame = 64 * 1024

var (
	ErrEmptyFrame    = errors.New("empty frame")
	ErrFrameTooLarge = fmt.Errorf("frame larger than %d bytes", MaxFrame)
)

// ReadFrame reads one length-prefixed payload: a 4-byte big-endian size
// followed by exactly that many bytes.
func ReadFrame(r io.Reader, max uint32) ([]byte, error) {
	var head [4]byte
	if _, err := io.ReadFull(r, head[:]); err != nil {
		return nil, err
	}
	size := binary.BigEndian.Uint32(head[:])
	if size == 0 {
		return nil, ErrEmptyFrame
	}
	if size > max {
		return nil, ErrFrameTooLarge
	}
	payload := make([]byte, size)
	if _, err := io.ReadFull(r, payload); err != nil {
		return nil, err
	}
	return payload, nil
}

// WriteFrame writes one length-prefixed payload in a single Write call, so a
// slow reader cannot see a header without its body.
func WriteFrame(w io.Writer, payload []byte) error {
	if len(payload) == 0 {
		return ErrEmptyFrame
	}
	if len(payload) > MaxFrame {
		return ErrFrameTooLarge
	}
	frame := make([]byte, 4+len(payload))
	binary.BigEndian.PutUint32(frame[:4], uint32(len(payload)))
	copy(frame[4:], payload)
	_, err := w.Write(frame)
	return err
}
