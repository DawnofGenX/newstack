package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestHealth(t *testing.T) {
	h := NewHandler()
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	req.Header.Set("Authorization", "Bearer secret-token")
	rr := httptest.NewRecorder()
	h.ServeHTTP(rr, req)
	if rr.Code != http.StatusOK {
		t.Fatalf("status = %d", rr.Code)
	}
	var body map[string]string
	if err := json.Unmarshal(rr.Body.Bytes(), &body); err != nil || body["status"] != "ok" {
		t.Fatalf("body = %s", rr.Body.String())
	}
	if rr.Header().Get("X-Request-ID") == "" {
		t.Fatal("missing request id")
	}
}

func TestPanicRecovery(t *testing.T) {
	h := NewHandler()
	req := httptest.NewRequest(http.MethodGet, "/panic", nil)
	rr := httptest.NewRecorder()
	h.ServeHTTP(rr, req)
	if rr.Code != http.StatusInternalServerError {
		t.Fatalf("status = %d", rr.Code)
	}
	if !strings.Contains(rr.Body.String(), "internal_server_error") {
		t.Fatalf("body = %s", rr.Body.String())
	}
}

func TestMiddlewareRedactsAuthorization(t *testing.T) {
	h := NewHandler()
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	req.Header.Set("Authorization", "Bearer secret-token")
	rr := httptest.NewRecorder()
	h.ServeHTTP(rr, req)
	if strings.Contains(rr.Body.String(), "secret-token") {
		t.Fatal("token leaked in body")
	}
}