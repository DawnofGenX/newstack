package main

import (
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func newSigner(now time.Time) URLSigner {
	return URLSigner{Secret: []byte("test-secret"), Now: func() time.Time { return now }}
}

func TestSignedURLCarriesSigAndExp(t *testing.T) {
	now := time.Unix(1_700_000_000, 0).UTC()
	s := newSigner(now)
	signed, err := s.SignedURL("GET", "/files/report.pdf", time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	req := httptest.NewRequest("GET", signed, nil)
	if got := req.URL.Query().Get("exp"); got != "1700000060" {
		t.Fatalf("exp = %q", got)
	}
	if req.URL.Query().Get("sig") == "" {
		t.Fatal("missing sig")
	}
	if err := s.VerifyRequest(req); err != nil {
		t.Fatalf("verify: %v", err)
	}
}

func TestExpiredSignatureIsRejected(t *testing.T) {
	base := time.Unix(1_700_000_000, 0).UTC()
	signed, err := newSigner(base).SignedURL("GET", "/files/a", 10*time.Second)
	if err != nil {
		t.Fatal(err)
	}
	later := newSigner(base.Add(11 * time.Second))
	req := httptest.NewRequest("GET", signed, nil)
	if err := later.VerifyRequest(req); !errors.Is(err, ErrExpired) {
		t.Fatalf("err = %v, want ErrExpired", err)
	}
}

func TestTamperedPathIsRejected(t *testing.T) {
	now := time.Unix(1_700_000_000, 0).UTC()
	s := newSigner(now)
	signed, err := s.SignedURL("GET", "/files/a", time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	tampered := signed[:len("/files/a")] + "-evil" + signed[len("/files/a"):]
	req := httptest.NewRequest("GET", tampered, nil)
	if err := s.VerifyRequest(req); !errors.Is(err, ErrBadSignature) {
		t.Fatalf("err = %v, want ErrBadSignature", err)
	}
}

func TestWrongMethodAndSecretAreRejected(t *testing.T) {
	now := time.Unix(1_700_000_000, 0).UTC()
	s := newSigner(now)
	signed, err := s.SignedURL("GET", "/files/a", time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	post := httptest.NewRequest("POST", signed, nil)
	if err := s.VerifyRequest(post); !errors.Is(err, ErrBadSignature) {
		t.Fatalf("method: err = %v", err)
	}
	other := URLSigner{Secret: []byte("other"), Now: func() time.Time { return now }}
	if err := other.VerifyRequest(httptest.NewRequest("GET", signed, nil)); !errors.Is(err, ErrBadSignature) {
		t.Fatalf("secret: err = %v", err)
	}
}

func TestMissingAndMalformedParameters(t *testing.T) {
	now := time.Unix(1_700_000_000, 0).UTC()
	s := newSigner(now)
	if err := s.VerifyRequest(httptest.NewRequest("GET", "/files/a", nil)); !errors.Is(err, ErrMissingSignature) {
		t.Fatalf("err = %v, want ErrMissingSignature", err)
	}
	if err := s.VerifyRequest(httptest.NewRequest("GET", "/files/a?exp=nope&sig=x", nil)); !errors.Is(err, ErrBadRequest) {
		t.Fatalf("err = %v, want ErrBadRequest", err)
	}
}

func TestHandlerGatesOnSignature(t *testing.T) {
	now := time.Unix(1_700_000_000, 0).UTC()
	s := newSigner(now)
	srv := httptest.NewServer(s.Handler(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})))
	defer srv.Close()

	signed, err := s.SignedURL("GET", "/files/a", time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	ok, err := http.Get(srv.URL + signed)
	if err != nil {
		t.Fatal(err)
	}
	ok.Body.Close()
	if ok.StatusCode != http.StatusOK {
		t.Fatalf("signed request status = %d", ok.StatusCode)
	}

	bad, err := http.Get(srv.URL + "/files/a")
	if err != nil {
		t.Fatal(err)
	}
	bad.Body.Close()
	if bad.StatusCode != http.StatusForbidden {
		t.Fatalf("unsigned request status = %d", bad.StatusCode)
	}
}
