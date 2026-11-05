package main

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
	"strings"
)

// TraceContext is the W3C traceparent a request arrived with (or the root we minted).
type TraceContext struct {
	TraceID string
	SpanID  string
	Flags   byte
}

// ErrTraceparent marks a header that cannot be parsed. The caller decides whether that
// is a 400 or a fresh root; this package never guesses.
var ErrTraceparent = errors.New("invalid traceparent")

const (
	traceIDBytes = 16
	spanIDBytes  = 8
	flagSampled  = 0x01
)

func randomHex(size int) string {
	buf := make([]byte, size)
	if _, err := rand.Read(buf); err != nil {
		panic(err) // crypto/rand failing means the box is broken
	}
	return hex.EncodeToString(buf)
}

// NewRoot mints a trace that starts here, flagged sampled.
func NewRoot() TraceContext {
	return TraceContext{TraceID: randomHex(traceIDBytes), SpanID: randomHex(spanIDBytes), Flags: flagSampled}
}

// Child keeps the trace id and flags and mints a new span id.
func (c TraceContext) Child() TraceContext {
	return TraceContext{TraceID: c.TraceID, SpanID: randomHex(spanIDBytes), Flags: c.Flags}
}

func (c TraceContext) Sampled() bool { return c.Flags&flagSampled == flagSampled }

// String renders the header value. flags are printed as two lowercase hex digits.
func (c TraceContext) String() string {
	return fmt.Sprintf("00-%s-%s-%02x", c.TraceID, c.SpanID, c.Flags)
}

func isLowerHex(value string, size int) bool {
	if len(value) != size*2 || value != strings.ToLower(value) {
		return false
	}
	for _, char := range value {
		if !((char >= '0' && char <= '9') || (char >= 'a' && char <= 'f')) {
			return false
		}
	}
	return true
}

func allZero(value string) bool {
	return strings.Trim(value, "0") == ""
}

// ParseTraceparent reads the header strictly: version 00, lowercase hex, four fields,
// and neither id may be all zeros. Anything else is ErrTraceparent with a reason the
// API can show.
func ParseTraceparent(header string) (TraceContext, error) {
	trimmed := strings.TrimSpace(header)
	if trimmed == "" {
		return TraceContext{}, fmt.Errorf("%w: the header is empty", ErrTraceparent)
	}
	parts := strings.Split(trimmed, "-")
	if len(parts) != 4 {
		return TraceContext{}, fmt.Errorf("%w: want 4 dash-separated fields, got %d", ErrTraceparent, len(parts))
	}
	version, traceID, spanID, flags := parts[0], parts[1], parts[2], parts[3]
	if version != "00" {
		return TraceContext{}, fmt.Errorf("%w: unsupported version %q", ErrTraceparent, version)
	}
	if !isLowerHex(traceID, traceIDBytes) {
		return TraceContext{}, fmt.Errorf("%w: the trace id must be 32 lowercase hex digits", ErrTraceparent)
	}
	if allZero(traceID) {
		return TraceContext{}, fmt.Errorf("%w: the trace id must not be all zeros", ErrTraceparent)
	}
	if !isLowerHex(spanID, spanIDBytes) {
		return TraceContext{}, fmt.Errorf("%w: the span id must be 16 lowercase hex digits", ErrTraceparent)
	}
	if allZero(spanID) {
		return TraceContext{}, fmt.Errorf("%w: the span id must not be all zeros", ErrTraceparent)
	}
	if !isLowerHex(flags, 1) {
		return TraceContext{}, fmt.Errorf("%w: the flags must be two lowercase hex digits", ErrTraceparent)
	}
	decoded, err := hex.DecodeString(flags)
	if err != nil {
		return TraceContext{}, fmt.Errorf("%w: %s", ErrTraceparent, err)
	}
	return TraceContext{TraceID: traceID, SpanID: spanID, Flags: decoded[0]}, nil
}
