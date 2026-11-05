package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// checker mirrors the other stacks' harnesses: one line per check, a count at
// the end, exit code 1 if anything failed.
type checker struct {
	total  int
	failed int
}

func (c *checker) check(name string, ok bool, detail string) {
	c.total++
	if ok {
		fmt.Printf("ok %d %s\n", c.total, name)
		return
	}
	c.failed++
	if detail != "" {
		fmt.Printf("FAIL %d %s: %s\n", c.total, name, detail)
		return
	}
	fmt.Printf("FAIL %d %s\n", c.total, name)
}

// fixedClock returns a clock the checks can move.
func fixedClock(start time.Time) (func() time.Time, func(time.Duration)) {
	current := start
	return func() time.Time { return current }, func(step time.Duration) { current = current.Add(step) }
}

// call performs one request against the handler and returns status + decoded body.
func call(h http.Handler, method, target, body string, headers map[string]string) (int, map[string]any) {
	var reader io.Reader
	if body != "" {
		reader = strings.NewReader(body)
	}
	request := httptest.NewRequest(method, target, reader)
	if body != "" {
		request.Header.Set("Content-Type", "application/json")
	}
	for key, value := range headers {
		request.Header.Set(key, value)
	}
	recorder := httptest.NewRecorder()
	h.ServeHTTP(recorder, request)
	var decoded map[string]any
	_ = json.Unmarshal(recorder.Body.Bytes(), &decoded)
	return recorder.Code, decoded
}

func stringField(body map[string]any, name string) string {
	value, _ := body[name].(string)
	return value
}

func numberField(body map[string]any, name string) float64 {
	value, _ := body[name].(float64)
	return value
}

func runSelftest() int {
	c := &checker{}

	// ---- tokens ---------------------------------------------------------
	clock, advance := fixedClock(time.Date(2026, 1, 1, 12, 0, 0, 0, time.UTC))
	tokens := newTokenizer([]byte("selftest-secret"), time.Minute, clock)

	token, claims, err := tokens.Issue("ada@example.com")
	c.check("issue returns a token", err == nil && token != "", "issue failed")
	c.check("token has three parts", len(strings.Split(token, ".")) == 3, "wrong number of segments")
	c.check("claims name the subject", claims.Subject == "ada@example.com", "subject lost")
	c.check("expires equals issued plus ttl", claims.Expires-claims.Issued == 60, "ttl not applied")

	back, err := tokens.Verify(token)
	c.check("verify accepts a fresh token", err == nil, fmt.Sprintf("%v", err))
	c.check("verify round-trips the subject", back.Subject == "ada@example.com", "subject changed")

	parts := strings.Split(token, ".")
	forged := parts[0] + "." + parts[1] + ".AAAA"
	if _, err := tokens.Verify(forged); err == nil {
		c.check("verify rejects a forged signature", false, "forged tag accepted")
	} else {
		c.check("verify rejects a forged signature", true, "")
	}

	other := newTokenizer([]byte("another-secret"), time.Minute, clock)
	if _, err := other.Verify(token); err == nil {
		c.check("verify rejects a token from another key", false, "foreign token accepted")
	} else {
		c.check("verify rejects a token from another key", true, "")
	}

	tampered := parts[0] + "." + b64.EncodeToString([]byte(`{"sub":"root@example.com","iat":1,"exp":9999999999}`)) + "." + parts[2]
	if _, err := tokens.Verify(tampered); err == nil {
		c.check("verify rejects a rewritten payload", false, "payload swap accepted")
	} else {
		c.check("verify rejects a rewritten payload", true, "")
	}

	if _, err := tokens.Verify("not-a-token"); err == nil {
		c.check("verify rejects garbage", false, "garbage accepted")
	} else {
		c.check("verify rejects garbage", true, "")
	}

	advance(2 * time.Minute)
	if _, err := tokens.Verify(token); err == nil {
		c.check("verify rejects an expired token", false, "expired token accepted")
	} else {
		c.check("verify rejects an expired token", true, "")
	}

	// ---- bearer ---------------------------------------------------------
	if got, err := bearer("Bearer abc.def.ghi"); err == nil && got == "abc.def.ghi" {
		c.check("bearer accepts the scheme case-insensitively", true, "")
	} else {
		c.check("bearer accepts the scheme case-insensitively", false, "scheme not folded")
	}
	if got, err := bearer("bearer   spaced"); err == nil && got == "spaced" {
		c.check("bearer trims surrounding spaces", true, "")
	} else {
		c.check("bearer trims surrounding spaces", false, got)
	}
	if _, err := bearer("Token abc"); err == nil {
		c.check("bearer rejects a foreign scheme", false, "Token accepted")
	} else {
		c.check("bearer rejects a foreign scheme", true, "")
	}
	if _, err := bearer("Bearer"); err == nil {
		c.check("bearer rejects a bare scheme", false, "empty token accepted")
	} else {
		c.check("bearer rejects a bare scheme", true, "")
	}

	// ---- passwords ------------------------------------------------------
	digest, err := hashPassword("correct horse battery")
	c.check("hash has four segments", err == nil && strings.Count(digest, "$") == 3, digest)
	c.check("hash names its algorithm", strings.HasPrefix(digest, "pbkdf2-sha256$"), digest)
	c.check("hash verifies the right password", verifyPassword("correct horse battery", digest), "digest rejected")
	c.check("hash rejects the wrong password", !verifyPassword("correct horse batterY", digest), "wrong password accepted")
	if _, err := hashPassword("short"); err == ErrWeakPassword {
		c.check("hash refuses a weak password", true, "")
	} else {
		c.check("hash refuses a weak password", false, "short password hashed")
	}
	if _, err := hashPassword("12345678"); err != nil {
		c.check("hash accepts eight characters", false, "eight characters refused")
	} else {
		c.check("hash accepts eight characters", true, "")
	}
	second, _ := hashPassword("correct horse battery")
	c.check("two hashes of one password differ", digest != second, "salt not random")
	c.check("verify rejects a malformed digest", !verifyPassword("x", "plain-text"), "malformed digest accepted")

	// ---- store ----------------------------------------------------------
	dir, err := os.MkdirTemp("", "jwt-store-*")
	if err != nil {
		fmt.Printf("FAIL cannot create a temp dir: %v\n", err)
		return 1
	}
	defer os.RemoveAll(dir)
	path := filepath.Join(dir, "users.json")

	store, err := NewStore(path)
	c.check("store starts empty", err == nil && store.Count() == 0, "store not empty")
	user, err := store.Add("Ada@Example.com", digest, "2026-01-01T00:00:00Z")
	c.check("add returns the first id", err == nil && user.ID == 1, fmt.Sprintf("%v", err))
	c.check("add keeps the given spelling", user.Email == "Ada@Example.com", user.Email)
	if _, err := store.Add("ada@example.com", digest, "2026-01-01T00:00:00Z"); err != ErrDuplicate {
		c.check("add refuses a duplicate email", false, "duplicate accepted")
	} else {
		c.check("add refuses a duplicate email", true, "")
	}
	if found, ok := store.Lookup("ADA@example.COM"); !ok || found.ID != user.ID {
		c.check("lookup ignores case", false, "case-sensitive lookup")
	} else {
		c.check("lookup ignores case", true, "")
	}
	if err := store.Save(); err != nil {
		c.check("save writes the file", false, fmt.Sprintf("%v", err))
	} else {
		c.check("save writes the file", true, "")
	}
	reopened, err := NewStore(path)
	c.check("a reopened store keeps its users", err == nil && reopened.Count() == 1, "count lost")
	if found, ok := reopened.Lookup("ada@example.com"); !ok || found.Digest != digest {
		c.check("a reopened store keeps the digest", false, "digest lost")
	} else {
		c.check("a reopened store keeps the digest", true, "")
	}

	broken := filepath.Join(dir, "broken.json")
	if err := os.WriteFile(broken, []byte("{not json"), 0o644); err != nil {
		c.check("a corrupt store refuses to open", false, "cannot write the fixture")
	} else if _, err := NewStore(broken); err == nil {
		c.check("a corrupt store refuses to open", false, "corrupt file accepted")
	} else {
		c.check("a corrupt store refuses to open", true, "")
	}

	// ---- handlers -------------------------------------------------------
	hclock, _ := fixedClock(time.Date(2026, 1, 1, 12, 0, 0, 0, time.UTC))
	memory, _ := NewStore("")
	h := &handler{store: memory, tokens: newTokenizer([]byte("handler-secret"), time.Minute, hclock), now: hclock}

	status, body := call(h, http.MethodGet, "/health", "", nil)
	c.check("health answers 200", status == 200, fmt.Sprintf("status %d", status))
	c.check("health counts zero accounts", numberField(body, "users") == 0, "count wrong")

	status, body = call(h, http.MethodPost, "/register", `{"email":"ada@example.com","password":"correct horse"}`, nil)
	c.check("register answers 201", status == 201, fmt.Sprintf("status %d", status))
	c.check("register echoes the email", stringField(body, "email") == "ada@example.com", stringField(body, "email"))
	c.check("register assigns id 1", numberField(body, "id") == 1, "id wrong")

	status, body = call(h, http.MethodPost, "/register", `{"email":"ada@example.com","password":"correct horse"}`, nil)
	c.check("a second register answers 409", status == 409, fmt.Sprintf("status %d", status))
	c.check("a taken email reports email_taken", stringField(body, "error") == "email_taken", stringField(body, "error"))

	status, body = call(h, http.MethodPost, "/register", `{"email":"new@example.com","password":"short"}`, nil)
	c.check("a weak password answers 422", status == 422, fmt.Sprintf("status %d", status))
	c.check("a weak password reports weak_password", stringField(body, "error") == "weak_password", stringField(body, "error"))

	status, body = call(h, http.MethodPost, "/register", `{"email":"new@example.com"}`, nil)
	c.check("a missing password answers 422", status == 422, fmt.Sprintf("status %d", status))
	c.check("a missing password reports missing_password", stringField(body, "error") == "missing_password", stringField(body, "error"))

	status, body = call(h, http.MethodPost, "/register", `{"email":"not-an-email","password":"correct horse"}`, nil)
	c.check("a bad email reports invalid_email", status == 422 && stringField(body, "error") == "invalid_email", stringField(body, "error"))

	status, body = call(h, http.MethodPost, "/register", `{"email":`, nil)
	c.check("broken JSON reports invalid_json", status == 422 && stringField(body, "error") == "invalid_json", stringField(body, "error"))

	status, body = call(h, http.MethodPost, "/login", `{"email":"ada@example.com","password":"correct horse"}`, nil)
	c.check("login answers 200", status == 200, fmt.Sprintf("status %d", status))
	issued := stringField(body, "token")
	c.check("login returns a token", issued != "", "no token")
	c.check("login names the scheme", stringField(body, "token_type") == "Bearer", stringField(body, "token_type"))
	c.check("login reports the deadline", numberField(body, "expires_at") > 0, "no expires_at")

	status, body = call(h, http.MethodPost, "/login", `{"email":"ada@example.com","password":"wrong horse"}`, nil)
	c.check("a wrong password answers 401", status == 401, fmt.Sprintf("status %d", status))
	c.check("a wrong password reports bad_credentials", stringField(body, "error") == "bad_credentials", stringField(body, "error"))

	status, body = call(h, http.MethodPost, "/login", `{"email":"ghost@example.com","password":"correct horse"}`, nil)
	c.check("an unknown email answers the same 401", status == 401 && stringField(body, "error") == "bad_credentials", stringField(body, "error"))

	status, body = call(h, http.MethodGet, "/me", "", map[string]string{"Authorization": "Bearer " + issued})
	c.check("me answers 200 for a fresh token", status == 200, fmt.Sprintf("status %d", status))
	c.check("me names the account", stringField(body, "email") == "ada@example.com", stringField(body, "email"))

	status, body = call(h, http.MethodGet, "/me", "", nil)
	c.check("me without a header answers 401", status == 401, fmt.Sprintf("status %d", status))
	c.check("me without a header reports missing_token", stringField(body, "error") == "missing_token", stringField(body, "error"))

	status, body = call(h, http.MethodGet, "/me", "", map[string]string{"Authorization": "Basic abc"})
	c.check("me with a foreign scheme reports malformed_token", status == 401 && stringField(body, "error") == "malformed_token", stringField(body, "error"))

	status, body = call(h, http.MethodGet, "/me", "", map[string]string{"Authorization": "Bearer " + issued + "x"})
	c.check("me rejects a tampered token", status == 401 && stringField(body, "error") == "invalid_token", stringField(body, "error"))

	status, body = call(h, http.MethodGet, "/nope", "", nil)
	c.check("an unknown path answers 404", status == 404, fmt.Sprintf("status %d", status))
	c.check("an unknown path names the request", stringField(body, "detail") == "no route for GET /nope", stringField(body, "detail"))

	status, body = call(h, http.MethodPost, "/health", "", nil)
	c.check("a wrong method answers 405", status == 405 && stringField(body, "error") == "method_not_allowed", stringField(body, "error"))

	// One token, one account, one process: a token for a deleted account must
	// stop working, so /me looks the user up instead of trusting the claims.
	empty := &handler{store: func() *Store { s, _ := NewStore(""); return s }(), tokens: newTokenizer([]byte("handler-secret"), time.Minute, hclock), now: hclock}
	status, body = call(empty, http.MethodGet, "/me", "", map[string]string{"Authorization": "Bearer " + issued})
	c.check("me rejects a token whose account is gone", status == 401 && stringField(body, "error") == "invalid_token", stringField(body, "error"))

	fmt.Printf("checks: %d, failed: %d\n", c.total, c.failed)
	if c.failed > 0 {
		return 1
	}
	fmt.Println("checks: all passed")
	return 0
}
