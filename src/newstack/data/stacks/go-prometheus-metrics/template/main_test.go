package main

import (
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/prometheus/client_golang/prometheus/promhttp"
)

func TestHealth(t *testing.T) {
	rr := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	health(rr, req)
	if rr.Code != http.StatusOK {
		t.Fatalf("health status = %d", rr.Code)
	}
}

func TestMetricsExposition(t *testing.T) {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", health)
	mux.Handle("/metrics", promhttp.Handler())
	srv := httptest.NewServer(instrument(mux))
	defer srv.Close()

	resp, err := http.Get(srv.URL + "/health")
	if err != nil {
		t.Fatal(err)
	}
	resp.Body.Close()

	resp, err = http.Get(srv.URL + "/metrics")
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	text := string(body)
	if !strings.Contains(text, "http_requests_total") {
		t.Fatalf("missing counter: %s", text)
	}
	if !strings.Contains(text, "http_request_duration_seconds") {
		t.Fatalf("missing histogram: %s", text)
	}
	if !strings.Contains(resp.Header.Get("Content-Type"), "text/plain") {
		t.Fatalf("bad content type: %s", resp.Header.Get("Content-Type"))
	}
}
