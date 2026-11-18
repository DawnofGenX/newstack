package main

import (
	"encoding/json"
	"net"
	"net/http"
	"os"
	"strconv"
	"strings"
)

// TokenBucketLimiter is a per-client token bucket middleware.
type TokenBucketLimiter struct {
	rate  float64
	burst int
}

func NewTokenBucketLimiter(rate float64, burst int) *TokenBucketLimiter {
	return &TokenBucketLimiter{rate: rate, burst: burst}
}

func (l *TokenBucketLimiter) Middleware(next http.Handler) http.Handler {
	buckets := newBucketStore(l.rate, l.burst)
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		key := r.RemoteAddr
		if host, _, err := net.SplitHostPort(key); err == nil {
			key = host
		} else if strings.Contains(key, ":") {
			key = strings.SplitN(key, ":", 2)[0]
		}
		if !buckets.allow(key) {
			w.Header().Set("Retry-After", "1")
			w.WriteHeader(http.StatusTooManyRequests)
			_ = json.NewEncoder(w).Encode(map[string]string{"error": "rate limited"})
			return
		}
		next.ServeHTTP(w, r)
	})
}

func health(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}

func limited(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "5540"
	}
	if _, err := strconv.Atoi(port); err != nil {
		port = "5540"
	}
	mux := http.NewServeMux()
	mux.HandleFunc("/health", health)
	limiter := NewTokenBucketLimiter(1, 2)
	mux.Handle("/limited", limiter.Middleware(http.HandlerFunc(limited)))
	if err := http.ListenAndServe(":"+port, mux); err != nil {
		panic(err)
	}
}
