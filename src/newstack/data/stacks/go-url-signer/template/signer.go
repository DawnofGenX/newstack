package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"errors"
	"fmt"
	"net/http"
	"net/url"
	"strconv"
	"time"
)

// Errors returned by verification.
var (
	ErrMissingSignature = errors.New("missing signature parameters")
	ErrExpired          = errors.New("signature expired")
	ErrBadSignature     = errors.New("signature mismatch")
	ErrBadRequest       = errors.New("malformed signature parameters")
)

// URLSigner signs a method plus path with an expiry, using HMAC-SHA256.
type URLSigner struct {
	Secret []byte
	Now    func() time.Time
}

func (s URLSigner) now() time.Time {
	if s.Now != nil {
		return s.Now()
	}
	return time.Now()
}

func (s URLSigner) signature(method, path, exp string) string {
	mac := hmac.New(sha256.New, s.Secret)
	fmt.Fprintf(mac, "%s\n%s\n%s", method, path, exp)
	return base64.RawURLEncoding.EncodeToString(mac.Sum(nil))
}

// SignedURL returns path with sig and exp query parameters attached.
func (s URLSigner) SignedURL(method, path string, ttl time.Duration) (string, error) {
	if method == "" || path == "" {
		return "", errors.New("method and path are required")
	}
	if ttl <= 0 {
		return "", errors.New("ttl must be positive")
	}
	exp := strconv.FormatInt(s.now().Add(ttl).Unix(), 10)
	sig := s.signature(method, path, exp)
	sep := "?"
	if u, err := url.Parse(path); err == nil && u.RawQuery != "" {
		sep = "&"
	}
	return path + sep + "exp=" + url.QueryEscape(exp) + "&sig=" + url.QueryEscape(sig), nil
}

// VerifyRequest checks the sig and exp parameters of an incoming request.
func (s URLSigner) VerifyRequest(r *http.Request) error {
	q := r.URL.Query()
	sig := q.Get("sig")
	exp := q.Get("exp")
	if sig == "" || exp == "" {
		return ErrMissingSignature
	}
	deadline, err := strconv.ParseInt(exp, 10, 64)
	if err != nil {
		return ErrBadRequest
	}
	if s.now().Unix() > deadline {
		return ErrExpired
	}
	expected := s.signature(r.Method, r.URL.Path, exp)
	if !hmac.Equal([]byte(expected), []byte(sig)) {
		return ErrBadSignature
	}
	return nil
}

// Handler serves content only for correctly signed requests.
func (s URLSigner) Handler(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if err := s.VerifyRequest(r); err != nil {
			status := http.StatusForbidden
			if errors.Is(err, ErrBadRequest) {
				status = http.StatusBadRequest
			}
			http.Error(w, err.Error(), status)
			return
		}
		next.ServeHTTP(w, r)
	})
}
