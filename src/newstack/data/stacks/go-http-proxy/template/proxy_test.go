package main

import (
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestHealth(t *testing.T) {
	rr := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	health(rr, req)
	if rr.Code != http.StatusOK {
		t.Fatalf("health status = %d", rr.Code)
	}
}

func TestProxyForwards(t *testing.T) {
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("X-Seen-XFF", r.Header.Get("X-Forwarded-For"))
		w.Header().Set("X-Seen-Connection", r.Header.Get("Connection"))
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("upstream-ok"))
	}))
	defer upstream.Close()

	proxy := httptest.NewServer(NewProxy(upstream.URL))
	defer proxy.Close()

	req, _ := http.NewRequest(http.MethodGet, proxy.URL+"/foo", nil)
	req.Header.Set("Connection", "keep-alive")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if string(body) != "upstream-ok" {
		t.Fatalf("body = %q", string(body))
	}
	if resp.Header.Get("X-Seen-XFF") == "" {
		t.Fatal("X-Forwarded-For not injected")
	}
	if resp.Header.Get("X-Seen-Connection") != "" {
		t.Fatalf("hop-by-hop Connection forwarded: %q", resp.Header.Get("X-Seen-Connection"))
	}
}
