package main

import (
	"crypto/rand"
	"errors"
	"fmt"
	"math/big"
	"strings"
	"time"
)

// crockford is the base32 alphabet used by ULIDs.
const crockford = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

// ulidLen is the fixed length of an encoded ULID.
const ulidLen = 26

// ErrInvalidULID is returned when a string is not a canonical ULID.
var ErrInvalidULID = errors.New("invalid ulid")

var decodeTable = buildDecodeTable()

func buildDecodeTable() [256]int8 {
	var table [256]int8
	for i := range table {
		table[i] = -1
	}
	for i := 0; i < len(crockford); i++ {
		table[crockford[i]] = int8(i)
	}
	return table
}

func encode(raw []byte) string {
	n := new(big.Int).SetBytes(raw)
	base := big.NewInt(32)
	mod := new(big.Int)
	out := make([]byte, ulidLen)
	for i := ulidLen - 1; i >= 0; i-- {
		n.DivMod(n, base, mod)
		out[i] = crockford[mod.Int64()]
	}
	return string(out)
}

func decode(text string) ([]byte, error) {
	if len(text) != ulidLen {
		return nil, fmt.Errorf("%w: length %d, want %d", ErrInvalidULID, len(text), ulidLen)
	}
	n := new(big.Int)
	base := big.NewInt(32)
	for i := 0; i < len(text); i++ {
		v := decodeTable[text[i]]
		if v < 0 {
			return nil, fmt.Errorf("%w: %q is not in the crockford alphabet", ErrInvalidULID, string(text[i]))
		}
		n.Mul(n, base)
		n.Add(n, big.NewInt(int64(v)))
	}
	out := n.Bytes()
	padded := make([]byte, 16)
	copy(padded[16-len(out):], out)
	return padded, nil
}

// NewFrom builds a ULID from an explicit timestamp and 10 byte entropy.
func NewFrom(at time.Time, entropy [10]byte) string {
	raw := make([]byte, 16)
	ms := uint64(at.UnixMilli())
	for i := 0; i < 6; i++ {
		raw[i] = byte(ms >> (8 * (5 - i)))
	}
	copy(raw[6:], entropy[:])
	return encode(raw)
}

// New builds a ULID for the given time with crypto/rand entropy.
func New(at time.Time) (string, error) {
	var entropy [10]byte
	if _, err := rand.Read(entropy[:]); err != nil {
		return "", err
	}
	return NewFrom(at, entropy), nil
}

// Timestamp returns the millisecond timestamp encoded in the ULID.
func Timestamp(text string) (time.Time, error) {
	raw, err := decode(strings.ToUpper(text))
	if err != nil {
		return time.Time{}, err
	}
	var ms uint64
	for i := 0; i < 6; i++ {
		ms = (ms << 8) | uint64(raw[i])
	}
	return time.UnixMilli(int64(ms)).UTC(), nil
}
