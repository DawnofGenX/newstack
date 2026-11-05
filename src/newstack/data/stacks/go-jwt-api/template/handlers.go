package main

import (
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"strings"
	"time"
)

const maxBody = 64 << 10

// reply is the only response shape: a client can always read {"error","detail"}.
type reply struct {
	Status int
	Body   map[string]any
}

type handler struct {
	store  *Store
	tokens *tokenizer
	now    func() time.Time
}

type credentials struct {
	Email    *string `json:"email"`
	Password *string `json:"password"`
}

// ServeHTTP lets the handler be mounted directly (the mux does this in server.go).
func (h *handler) ServeHTTP(w http.ResponseWriter, r *http.Request) { h.route(w, r) }

func (h *handler) route(w http.ResponseWriter, r *http.Request) {
	switch r.URL.Path {
	case "/health":
		h.readOnly(http.MethodGet, w, r, h.health)
	case "/register":
		h.readOnly(http.MethodPost, w, r, h.register)
	case "/login":
		h.readOnly(http.MethodPost, w, r, h.login)
	case "/me":
		h.readOnly(http.MethodGet, w, r, h.me)
	default:
		h.send(w, reply{Status: http.StatusNotFound, Body: map[string]any{
			"error":  "not_found",
			"detail": "no route for " + r.Method + " " + r.URL.Path,
		}})
	}
}

// readOnly answers 405 itself, so an unknown method never reaches a handler that
// would have to repeat the check.
func (h *handler) readOnly(method string, w http.ResponseWriter, r *http.Request, next func(*http.Request) reply) {
	if r.Method != method {
		h.send(w, reply{Status: http.StatusMethodNotAllowed, Body: map[string]any{
			"error":  "method_not_allowed",
			"detail": r.Method + " is not allowed here",
		}})
		return
	}
	h.send(w, next(r))
}

func (h *handler) send(w http.ResponseWriter, out reply) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(out.Status)
	encoder := json.NewEncoder(w)
	encoder.SetEscapeHTML(false)
	_ = encoder.Encode(out.Body)
}

func decodeCredentials(r *http.Request) (string, string, *reply) {
	limited := http.MaxBytesReader(nil, r.Body, maxBody)
	raw, err := io.ReadAll(limited)
	if err != nil {
		return "", "", &reply{Status: http.StatusRequestEntityTooLarge, Body: map[string]any{
			"error": "body_too_large", "detail": "the body must stay under 64 KiB",
		}}
	}
	var payload credentials
	if err := json.Unmarshal(raw, &payload); err != nil {
		return "", "", &reply{Status: http.StatusUnprocessableEntity, Body: map[string]any{
			"error": "invalid_json", "detail": "the request body must be JSON",
		}}
	}
	// A pointer distinguishes "absent" from "empty string": "" is a weak password,
	// but a missing field is a missing field, and the client should be told which.
	if payload.Email == nil {
		return "", "", &reply{Status: http.StatusUnprocessableEntity, Body: map[string]any{
			"error": "missing_email", "detail": "email is required",
		}}
	}
	if payload.Password == nil {
		return "", "", &reply{Status: http.StatusUnprocessableEntity, Body: map[string]any{
			"error": "missing_password", "detail": "password is required",
		}}
	}
	email := strings.TrimSpace(*payload.Email)
	if email == "" || !strings.Contains(email, "@") {
		return "", "", &reply{Status: http.StatusUnprocessableEntity, Body: map[string]any{
			"error": "invalid_email", "detail": "email must contain @",
		}}
	}
	return email, *payload.Password, nil
}

func (h *handler) health(*http.Request) reply {
	return reply{Status: http.StatusOK, Body: map[string]any{
		"status": "ok", "users": h.store.Count(),
	}}
}

func (h *handler) register(r *http.Request) reply {
	email, password, bad := decodeCredentials(r)
	if bad != nil {
		return *bad
	}
	digest, err := hashPassword(password)
	if errors.Is(err, ErrWeakPassword) {
		return reply{Status: http.StatusUnprocessableEntity, Body: map[string]any{
			"error": "weak_password", "detail": "password must be at least 8 characters",
		}}
	}
	if err != nil {
		return reply{Status: http.StatusInternalServerError, Body: map[string]any{
			"error": "hash_failed", "detail": "the password could not be hashed",
		}}
	}
	user, err := h.store.Add(email, digest, h.now().UTC().Format(time.RFC3339))
	if errors.Is(err, ErrDuplicate) {
		return reply{Status: http.StatusConflict, Body: map[string]any{
			"error": "email_taken", "detail": "that email is already registered",
		}}
	}
	if err != nil {
		return reply{Status: http.StatusInternalServerError, Body: map[string]any{
			"error": "store_failed", "detail": "the account could not be saved",
		}}
	}
	if err := h.store.Save(); err != nil {
		return reply{Status: http.StatusInternalServerError, Body: map[string]any{
			"error": "persist_failed", "detail": "the account could not be written to disk",
		}}
	}
	return reply{Status: http.StatusCreated, Body: map[string]any{
		"id": user.ID, "email": user.Email,
	}}
}

func (h *handler) login(r *http.Request) reply {
	email, password, bad := decodeCredentials(r)
	if bad != nil {
		return *bad
	}
	user, found := h.store.Lookup(email)
	// Same answer, same work: an unknown email must not be cheaper to reject than
	// a wrong password, or the endpoint becomes an account enumerator.
	if !found {
		verifyPassword(password, dummyDigest)
		return reply{Status: http.StatusUnauthorized, Body: map[string]any{
			"error": "bad_credentials", "detail": "email or password is wrong",
		}}
	}
	if !verifyPassword(password, user.Digest) {
		return reply{Status: http.StatusUnauthorized, Body: map[string]any{
			"error": "bad_credentials", "detail": "email or password is wrong",
		}}
	}
	token, claims, err := h.tokens.Issue(user.Email)
	if err != nil {
		return reply{Status: http.StatusInternalServerError, Body: map[string]any{
			"error": "issue_failed", "detail": "the token could not be signed",
		}}
	}
	return reply{Status: http.StatusOK, Body: map[string]any{
		"token": token, "token_type": "Bearer", "expires_at": claims.Expires,
	}}
}

func (h *handler) me(r *http.Request) reply {
	header := r.Header.Get("Authorization")
	if header == "" {
		return reply{Status: http.StatusUnauthorized, Body: map[string]any{
			"error": "missing_token", "detail": "send an Authorization header",
		}}
	}
	token, err := bearer(header)
	if err != nil {
		return reply{Status: http.StatusUnauthorized, Body: map[string]any{
			"error": "malformed_token", "detail": "expected: Bearer <token>",
		}}
	}
	claims, err := h.tokens.Verify(token)
	if err != nil {
		// One answer for every failure: expired, forged and truncated tokens are
		// all "invalid_token". A distinct message is a hint for an attacker.
		return reply{Status: http.StatusUnauthorized, Body: map[string]any{
			"error": "invalid_token", "detail": "the token is not valid",
		}}
	}
	user, found := h.store.Lookup(claims.Subject)
	if !found {
		return reply{Status: http.StatusUnauthorized, Body: map[string]any{
			"error": "invalid_token", "detail": "the token is not valid",
		}}
	}
	return reply{Status: http.StatusOK, Body: map[string]any{
		"id": user.ID, "email": user.Email, "issued_at": claims.Issued, "expires_at": claims.Expires,
	}}
}
