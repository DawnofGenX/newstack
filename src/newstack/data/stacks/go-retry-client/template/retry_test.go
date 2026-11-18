package main

import (
	"net/http"
	"net/http/httptest"
	"sync"
	"testing"
	"time"
)

func TestRetryThenSuccess(t *testing.T) {
	var calls int
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		calls++
		if calls < 3 {
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
		w.WriteHeader(http.StatusOK)
	}))
	defer srv.Close()

	var sleeps []time.Duration
	r := &Retryer{
		MaxAttempts: 5,
		BaseDelay:   time.Millisecond,
		MaxDelay:    10 * time.Millisecond,
		Jitter:      func(d time.Duration) time.Duration { return 0 },
		Sleep:       func(d time.Duration) { sleeps = append(sleeps, d) },
	}
	req, _ := http.NewRequest("GET", srv.URL, nil)
	resp, err := r.Do(req)
	if err != nil || resp.StatusCode != 200 {
		t.Fatalf("err=%v status=%v", err, resp)
	}
	if calls != 3 {
		t.Fatalf("calls=%d", calls)
	}
	if len(sleeps) != 2 {
		t.Fatalf("sleeps=%d", len(sleeps))
	}
}

func TestMaxAttempts(t *testing.T) {
	var calls int
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		calls++
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer srv.Close()

	r := &Retryer{
		MaxAttempts: 3,
		BaseDelay:   time.Millisecond,
		MaxDelay:    10 * time.Millisecond,
		Jitter:      func(d time.Duration) time.Duration { return 0 },
		Sleep:       func(d time.Duration) {},
	}
	req, _ := http.NewRequest("GET", srv.URL, nil)
	resp, err := r.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	if resp.StatusCode != 500 {
		t.Fatalf("status=%d", resp.StatusCode)
	}
	if calls != 3 {
		t.Fatalf("calls=%d", calls)
	}
}

func TestNonRetryable(t *testing.T) {
	var calls int
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		calls++
		w.WriteHeader(http.StatusNotFound)
	}))
	defer srv.Close()

	var mu sync.Mutex
	r := &Retryer{
		MaxAttempts: 5,
		BaseDelay:   time.Millisecond,
		MaxDelay:    10 * time.Millisecond,
		Jitter:      func(d time.Duration) time.Duration { return 0 },
		Sleep:       func(d time.Duration) { mu.Lock(); defer mu.Unlock() },
	}
	req, _ := http.NewRequest("GET", srv.URL, nil)
	resp, err := r.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	if resp.StatusCode != 404 {
		t.Fatalf("status=%d", resp.StatusCode)
	}
	if calls != 1 {
		t.Fatalf("calls=%d", calls)
	}
}