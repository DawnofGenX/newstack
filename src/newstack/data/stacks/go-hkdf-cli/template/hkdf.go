package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"errors"
	"fmt"
)

// HashLen is the output size of the underlying hash, SHA-256.
const HashLen = 32

// ErrLength refuses an output longer than one hash of counters can express.
var ErrLength = errors.New("hkdf: length must be between 1 and 8160 bytes")

// Extract runs HKDF-Extract: PRK = HMAC(salt, IKM). An empty salt becomes a
// block of zero bytes, as RFC 5869 section 2.2 requires.
func Extract(salt, ikm []byte) []byte {
	if len(salt) == 0 {
		salt = make([]byte, HashLen)
	}
	mac := hmac.New(sha256.New, salt)
	mac.Write(ikm)
	return mac.Sum(nil)
}

// Expand runs HKDF-Expand: T(n) = HMAC(PRK, T(n-1) || info || counter).
func Expand(prk, info []byte, length int) ([]byte, error) {
	if length < 1 || length > 255*HashLen {
		return nil, ErrLength
	}
	output := make([]byte, 0, length)
	var block []byte
	for counter := byte(1); len(output) < length; counter++ {
		mac := hmac.New(sha256.New, prk)
		mac.Write(block)
		mac.Write(info)
		mac.Write([]byte{counter})
		block = mac.Sum(nil)
		output = append(output, block...)
	}
	return output[:length], nil
}

// Derive is Extract followed by Expand, the whole RFC 5869 flow.
func Derive(salt, ikm, info []byte, length int) ([]byte, error) {
	return Expand(Extract(salt, ikm), info, length)
}

func run(args []string, stdin []byte) (string, error) {
	ikm := []byte(nil)
	var salt, info []byte
	length := HashLen

	for index := 0; index < len(args); index++ {
		switch args[index] {
		case "-h", "--help":
			return usage(), nil
		case "-salt":
			if index+1 >= len(args) {
				return "", fmt.Errorf("option %s needs a value", args[index])
			}
			index++
			decoded, err := decodeHex(args[index])
			if err != nil {
				return "", fmt.Errorf("salt: %w", err)
			}
			salt = decoded
		case "-info":
			if index+1 >= len(args) {
				return "", fmt.Errorf("option %s needs a value", args[index])
			}
			index++
			info = []byte(args[index])
		case "-length":
			if index+1 >= len(args) {
				return "", fmt.Errorf("option %s needs a value", args[index])
			}
			index++
			if _, err := fmt.Sscanf(args[index], "%d", &length); err != nil {
				return "", fmt.Errorf("length must be a number: %s", args[index])
			}
		default:
			if len(args[index]) > 0 && args[index][0] == '-' {
				return "", fmt.Errorf("unknown option %s", args[index])
			}
			if ikm != nil {
				return "", errors.New("only one input keying material may be given")
			}
			decoded, err := decodeHex(args[index])
			if err != nil {
				return "", fmt.Errorf("ikm: %w", err)
			}
			ikm = decoded
		}
	}

	if ikm == nil {
		if len(stdin) == 0 {
			return "", errors.New("no input keying material (pass hex or pipe bytes)")
		}
		ikm = stdin
	}

	derived, err := Derive(salt, ikm, info, length)
	if err != nil {
		return "", err
	}
	return fmt.Sprintf("%x", derived), nil
}

func usage() string {
	return "usage: hkdf-cli [-salt HEX] [-info TEXT] [-length N] IKM-HEX\n\n" +
		"Derives key material with HKDF-SHA256 (RFC 5869).\n" +
		"With no IKM argument the raw bytes of standard input are the IKM.\n" +
		"Exit status is 1 for bad input and 2 for bad usage."
}

func decodeHex(text string) ([]byte, error) {
	out := make([]byte, 0, len(text)/2)
	if len(text)%2 != 0 {
		return nil, fmt.Errorf("hex input must have an even number of digits, got %d", len(text))
	}
	for index := 0; index < len(text); index += 2 {
		var value byte
		if _, err := fmt.Sscanf(text[index:index+2], "%02x", &value); err != nil {
			return nil, fmt.Errorf("invalid hex at offset %d: %q", index, text[index:index+2])
		}
		out = append(out, value)
	}
	return out, nil
}
