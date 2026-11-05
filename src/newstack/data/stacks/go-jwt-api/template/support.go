package main

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
)

// dummyDigest is a real PBKDF2 digest for a password nobody knows. Login checks
// it when the email is unknown so that "no such account" costs the same 120,000
// iterations as "wrong password" — otherwise response time enumerates accounts.
var dummyDigest = mustDummyDigest()

func mustDummyDigest() string {
	if random, err := hashPassword(randomSecret()); err == nil {
		return random
	}
	// Hashing can only fail here if the platform's CSPRNG is broken; a fixed
	// digest is still better than skipping the work.
	return fmt.Sprintf("pbkdf2-sha256$%d$%s$%s", iterations,
		"00000000000000000000000000000000",
		"0000000000000000000000000000000000000000000000000000000000000000")
}

func randomSecret() string {
	buffer := make([]byte, 16)
	if _, err := rand.Read(buffer); err != nil {
		return "fallback-dummy-password-value"
	}
	return hex.EncodeToString(buffer)
}
