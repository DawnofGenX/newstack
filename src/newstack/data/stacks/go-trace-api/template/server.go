package main

import (
	"context"
	"fmt"
	"net"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"
)

type server struct {
	httpServer *http.Server
	listener   net.Listener
}

func newServer(tracker *Tracker, addr string) (*server, error) {
	listener, err := net.Listen("tcp", addr)
	if err != nil {
		return nil, err
	}
	httpServer := &http.Server{
		Handler:           newHandler(tracker),
		ReadHeaderTimeout: 5 * time.Second,
		IdleTimeout:       30 * time.Second,
	}
	return &server{httpServer: httpServer, listener: listener}, nil
}

func (s *server) addr() string { return s.listener.Addr().String() }

func (s *server) serve() error { return s.httpServer.Serve(s.listener) }

func (s *server) stop(ctx context.Context) error { return s.httpServer.Shutdown(ctx) }

// listenAndServe blocks until a signal arrives, then drains.
func listenAndServe(tracker *Tracker, addr string) error {
	srv, err := newServer(tracker, addr)
	if err != nil {
		return err
	}
	signals := make(chan os.Signal, 1)
	signal.Notify(signals, syscall.SIGINT, syscall.SIGTERM)
	done := make(chan error, 1)
	go func() { done <- srv.serve() }()
	select {
	case err := <-done:
		return err
	case received := <-signals:
		fmt.Fprintf(os.Stderr, "%s received: draining\n", received)
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		return srv.stop(ctx)
	}
}

func defaultAddr() string {
	host := envOr("HOST", "127.0.0.1")
	port := envOr("PORT", "5475")
	if _, err := strconv.Atoi(port); err != nil {
		fmt.Fprintf(os.Stderr, "PORT must be a number, got %q\n", port)
		os.Exit(2)
	}
	return net.JoinHostPort(host, port)
}

func envOr(name, fallback string) string {
	if value := os.Getenv(name); value != "" {
		return value
	}
	return fallback
}
