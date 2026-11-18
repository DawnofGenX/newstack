package main

import (
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
	requestsTotal = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "http_requests_total",
		Help: "Total number of HTTP requests.",
	})
	requestDuration = prometheus.NewHistogram(prometheus.HistogramOpts{
		Name:    "http_request_duration_seconds",
		Help:    "HTTP request duration in seconds.",
		Buckets: prometheus.DefBuckets,
	})
)

func init() {
	prometheus.MustRegister(requestsTotal, requestDuration)
}

func instrument(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		requestsTotal.Inc()
		next.ServeHTTP(w, r)
		requestDuration.Observe(time.Since(start).Seconds())
	})
}

func health(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(`{"status":"ok"}`))
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "5543"
	}
	if _, err := strconv.Atoi(port); err != nil {
		port = "5543"
	}
	mux := http.NewServeMux()
	mux.HandleFunc("/health", health)
	mux.Handle("/metrics", promhttp.Handler())
	if err := http.ListenAndServe(":"+port, instrument(mux)); err != nil {
		panic(err)
	}
}
