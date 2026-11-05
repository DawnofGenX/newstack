package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func newTestServer(t *testing.T) *httptest.Server {
	t.Helper()
	store, err := NewStore("")
	if err != nil {
		t.Fatalf("store: %v", err)
	}
	h := &handler{store: store, tokens: newTokenizer([]byte("test-secret"), time.Minute, time.Now), now: time.Now}
	return httptest.NewServer(h)
}

func do(t *testing.T, method, url, body string, headers map[string]string) (int, map[string]any) {
	t.Helper()
	var reader *strings.Reader
	if body != "" {
		reader = strings.NewReader(body)
	} else {
		reader = strings.NewReader("")
	}
	request, err := http.NewRequest(method, url, reader)
	if err != nil {
		t.Fatalf("request: %v", err)
	}
	for key, value := range headers {
		request.Header.Set(key, value)
	}
	response, err := http.DefaultClient.Do(request)
	if err != nil {
		t.Fatalf("do: %v", err)
	}
	defer response.Body.Close()
	var decoded map[string]any
	_ = json.NewDecoder(response.Body).Decode(&decoded)
	return response.StatusCode, decoded
}

func TestRegisterLoginAndMe(t *testing.T) {
	server := newTestServer(t)
	defer server.Close()

	status, body := do(t, http.MethodPost, server.URL+"/register", `{"email":"ada@example.com","password":"correct horse"}`, nil)
	if status != http.StatusCreated {
		t.Fatalf("register status = %d (%v)", status, body)
	}

	status, body = do(t, http.MethodPost, server.URL+"/login", `{"email":"ada@example.com","password":"correct horse"}`, nil)
	if status != http.StatusOK {
		t.Fatalf("login status = %d (%v)", status, body)
	}
	token, _ := body["token"].(string)
	if token == "" {
		t.Fatal("login returned no token")
	}

	status, body = do(t, http.MethodGet, server.URL+"/me", "", map[string]string{"Authorization": "Bearer " + token})
	if status != http.StatusOK {
		t.Fatalf("me status = %d (%v)", status, body)
	}
	if body["email"] != "ada@example.com" {
		t.Fatalf("me email = %v", body["email"])
	}
}

func TestExpiredTokenIsRejected(t *testing.T) {
	store, _ := NewStore("")
	clock := time.Date(2026, 1, 1, 0, 0, 0, 0, time.UTC)
	tokens := newTokenizer([]byte("test-secret"), time.Second, func() time.Time { return clock })
	h := &handler{store: store, tokens: tokens, now: func() time.Time { return clock }}
	server := httptest.NewServer(h)
	defer server.Close()

	if status, body := do(t, http.MethodPost, server.URL+"/register", `{"email":"ada@example.com","password":"correct horse"}`, nil); status != http.StatusCreated {
		t.Fatalf("register status = %d (%v)", status, body)
	}
	_, body := do(t, http.MethodPost, server.URL+"/login", `{"email":"ada@example.com","password":"correct horse"}`, nil)
	token, _ := body["token"].(string)

	clock = clock.Add(2 * time.Second)
	status, body := do(t, http.MethodGet, server.URL+"/me", "", map[string]string{"Authorization": "Bearer " + token})
	if status != http.StatusUnauthorized {
		t.Fatalf("expired token status = %d (%v)", status, body)
	}
	if body["error"] != "invalid_token" {
		t.Fatalf("expired token error = %v (a distinct message would leak token state)", body["error"])
	}
}

func TestUnknownAndWrongPasswordLookTheSame(t *testing.T) {
	server := newTestServer(t)
	defer server.Close()

	if status, _ := do(t, http.MethodPost, server.URL+"/register", `{"email":"ada@example.com","password":"correct horse"}`, nil); status != http.StatusCreated {
		t.Fatal("register failed")
	}
	statusA, bodyA := do(t, http.MethodPost, server.URL+"/login", `{"email":"ada@example.com","password":"nope nope"}`, nil)
	statusB, bodyB := do(t, http.MethodPost, server.URL+"/login", `{"email":"ghost@example.com","password":"nope nope"}`, nil)
	if statusA != statusB || statusA != http.StatusUnauthorized {
		t.Fatalf("statuses differ: %d vs %d", statusA, statusB)
	}
	if bodyA["detail"] != bodyB["detail"] || bodyA["error"] != bodyB["error"] {
		t.Fatalf("bodies differ: %v vs %v", bodyA, bodyB)
	}
}

func TestAccountsSurviveARestart(t *testing.T) {
	path := t.TempDir() + "/users.json"
	first, err := NewStore(path)
	if err != nil {
		t.Fatalf("store: %v", err)
	}
	digest, _ := hashPassword("correct horse")
	if _, err := first.Add("ada@example.com", digest, "2026-01-01T00:00:00Z"); err != nil {
		t.Fatalf("add: %v", err)
	}
	if err := first.Save(); err != nil {
		t.Fatalf("save: %v", err)
	}
	second, err := NewStore(path)
	if err != nil {
		t.Fatalf("reopen: %v", err)
	}
	user, ok := second.Lookup("ADA@example.com")
	if !ok || !verifyPassword("correct horse", user.Digest) {
		t.Fatal("the reopened store lost or corrupted the account")
	}
}

func TestTokenRoundTrip(t *testing.T) {
	now := time.Date(2026, 1, 1, 0, 0, 0, 0, time.UTC)
	tokens := newTokenizer([]byte("test-secret"), time.Minute, func() time.Time { return now })
	token, claims, err := tokens.Issue("ada@example.com")
	if err != nil {
		t.Fatalf("issue: %v", err)
	}
	back, err := tokens.Verify(token)
	if err != nil {
		t.Fatalf("verify: %v", err)
	}
	if back.Subject != claims.Subject || back.Expires != claims.Expires {
		t.Fatalf("claims changed: %+v vs %+v", back, claims)
	}
	if _, err := newTokenizer([]byte("other"), time.Minute, func() time.Time { return now }).Verify(token); err == nil {
		t.Fatal("a token verified under the wrong key")
	}
}
