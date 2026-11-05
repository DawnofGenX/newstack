package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"errors"
	"strconv"
	"strings"
	"time"
)

// ErrToken is returned for every way a token can be wrong. The caller must not
// tell the client which one it was: "expired" and "forged" are both 401s, and a
// distinct message for a bad signature is an oracle.
var ErrToken = errors.New("invalid token")

// Claims is the payload. exp is seconds since the epoch, not a duration: a
// duration would have to be interpreted against the issuer's clock, and a
// verifier in another process would have no idea when the token was minted.
type Claims struct {
	Subject string `json:"sub"`
	Issued  int64  `json:"iat"`
	Expires int64  `json:"exp"`
}

// Expired reports whether the claims are past their deadline at *now*.
func (c Claims) Expired(now time.Time) bool {
	return now.Unix() >= c.Expires
}

type tokenizer struct {
	secret []byte
	ttl    time.Duration
	now    func() time.Time
}

func newTokenizer(secret []byte, ttl time.Duration, now func() time.Time) *tokenizer {
	if now == nil {
		now = time.Now
	}
	return &tokenizer{secret: secret, ttl: ttl, now: now}
}

var b64 = base64.RawURLEncoding

// Issue mints a token: base64url(header).base64url(claims).base64url(mac).
func (t *tokenizer) Issue(subject string) (string, Claims, error) {
	if subject == "" {
		return "", Claims{}, errors.New("a token needs a subject")
	}
	issued := t.now()
	claims := Claims{Subject: subject, Issued: issued.Unix(), Expires: issued.Add(t.ttl).Unix()}
	payload, err := json.Marshal(claims)
	if err != nil {
		return "", Claims{}, err
	}
	header := b64.EncodeToString([]byte(`{"alg":"HS256","typ":"JWT"}`))
	body := b64.EncodeToString(payload)
	signing := header + "." + body
	mac := hmac.New(sha256.New, t.secret)
	mac.Write([]byte(signing))
	return signing + "." + b64.EncodeToString(mac.Sum(nil)), claims, nil
}

// Verify checks the shape, the signature (in constant time) and the deadline.
func (t *tokenizer) Verify(token string) (Claims, error) {
	parts := strings.Split(token, ".")
	if len(parts) != 3 {
		return Claims{}, ErrToken
	}
	signing := parts[0] + "." + parts[1]
	mac := hmac.New(sha256.New, t.secret)
	mac.Write([]byte(signing))
	want := mac.Sum(nil)
	got, err := b64.DecodeString(parts[2])
	if err != nil {
		return Claims{}, ErrToken
	}
	// Constant time: a byte-by-byte comparison leaks how much of a forged tag was
	// right, which is enough to forge the rest one byte at a time.
	if !hmac.Equal(got, want) {
		return Claims{}, ErrToken
	}
	payload, err := b64.DecodeString(parts[1])
	if err != nil {
		return Claims{}, ErrToken
	}
	var claims Claims
	if err := json.Unmarshal(payload, &claims); err != nil {
		return Claims{}, ErrToken
	}
	if claims.Subject == "" || claims.Expires == 0 {
		return Claims{}, ErrToken
	}
	if claims.Expired(t.now()) {
		return Claims{}, ErrToken
	}
	return claims, nil
}

// bearer extracts the token from an Authorization header value.
func bearer(header string) (string, error) {
	scheme, rest, found := strings.Cut(header, " ")
	if !found || !strings.EqualFold(scheme, "Bearer") {
		return "", ErrToken
	}
	token := strings.TrimSpace(rest)
	if token == "" {
		return "", ErrToken
	}
	return token, nil
}

// unixSeconds is a small helper the tests use to build claims without a clock.
func unixSeconds(seconds int64) string { return strconv.FormatInt(seconds, 10) }
