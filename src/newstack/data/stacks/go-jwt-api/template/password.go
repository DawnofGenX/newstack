package main

import (
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/hex"
	"errors"
	"fmt"
	"hash"
	"strings"
)

func newHMAC(key []byte) hash.Hash { return hmac.New(sha256.New, key) }

const (
	saltSize    = 16
	keySize     = 32
	iterations  = 120_000
	minPassword = 8
)

var (
	ErrWeakPassword = errors.New("weak password")
	ErrMalformed    = errors.New("malformed hash")
)

// hashPassword returns "pbkdf2-sha256$<iterations>$<salt hex>$<key hex>".
//
// The parameters travel with the digest: raising the iteration count later must
// not invalidate every stored password, and a verifier has to know which count
// produced the bytes it is comparing against.
func hashPassword(password string) (string, error) {
	if len([]rune(password)) < minPassword {
		return "", ErrWeakPassword
	}
	salt := make([]byte, saltSize)
	if _, err := rand.Read(salt); err != nil {
		return "", err
	}
	key := pbkdf2Key(password, salt, iterations, keySize)
	return fmt.Sprintf("pbkdf2-sha256$%d$%s$%s", iterations, hex.EncodeToString(salt), hex.EncodeToString(key)), nil
}

// verifyPassword recomputes the digest with the stored parameters.
func verifyPassword(password, stored string) bool {
	parts := strings.Split(stored, "$")
	if len(parts) != 4 || parts[0] != "pbkdf2-sha256" {
		return false
	}
	var rounds int
	if _, err := fmt.Sscanf(parts[1], "%d", &rounds); err != nil || rounds < 1000 {
		return false
	}
	salt, err := hex.DecodeString(parts[2])
	if err != nil {
		return false
	}
	want, err := hex.DecodeString(parts[3])
	if err != nil || len(want) == 0 {
		return false
	}
	got := pbkdf2Key(password, salt, rounds, len(want))
	// Constant time, again: a short-circuit comparison leaks a prefix.
	return subtle.ConstantTimeCompare(got, want) == 1
}

// pbkdf2Key is PBKDF2-HMAC-SHA256. It is written out rather than imported so the
// starter has no module dependencies; the loop is the whole of RFC 8018 §5.2.
func pbkdf2Key(password string, salt []byte, rounds, length int) []byte {
	blocks := (length + sha256.Size - 1) / sha256.Size
	out := make([]byte, 0, blocks*sha256.Size)
	pass := []byte(password)
	for block := 1; block <= blocks; block++ {
		mac := newHMAC(pass)
		mac.Write(salt)
		counter := []byte{byte(block >> 24), byte(block >> 16), byte(block >> 8), byte(block)}
		mac.Write(counter)
		u := mac.Sum(nil)
		t := make([]byte, len(u))
		copy(t, u)
		for round := 1; round < rounds; round++ {
			mac.Reset()
			mac.Write(u)
			u = mac.Sum(u[:0])
			for i := range t {
				t[i] ^= u[i]
			}
		}
		out = append(out, t...)
	}
	return out[:length]
}
