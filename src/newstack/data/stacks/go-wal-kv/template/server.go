package main

import (
	"context"
	"errors"
	"fmt"
	"net"
	"net/http"
	"os"
	"strconv"
	"time"
)

// Server owns the listener so tests can bind port 0 and read the real port.
type Server struct {
	http     *http.Server
	listener net.Listener
	store    *Store
}

// Listen binds addr and wires the handler. It returns the server with the port
// that was actually bound, which is how a test avoids port collisions.
func Listen(store *Store, addr string) (*Server, int, error) {
	listener, err := net.Listen("tcp", addr)
	if err != nil {
		return nil, 0, err
	}
	server := &Server{
		http: &http.Server{
			Handler:           newHandler(store),
			ReadHeaderTimeout: 5 * time.Second,
			IdleTimeout:       30 * time.Second,
		},
		listener: listener,
		store:    store,
	}
	port := listener.Addr().(*net.TCPAddr).Port
	return server, port, nil
}

// Serve blocks until the listener is closed.
func (s *Server) Serve() error {
	err := s.http.Serve(s.listener)
	if errors.Is(err, http.ErrServerClosed) {
		return nil
	}
	return err
}

// Shutdown stops accepting and waits for the in-flight requests.
func (s *Server) Shutdown(ctx context.Context) error {
	return s.http.Shutdown(ctx)
}

func parsePort(raw string) (int, error) {
	port, err := strconv.Atoi(raw)
	if err != nil {
		return 0, fmt.Errorf("PORT must be a number, got %q", raw)
	}
	if port < 1 || port > 65535 {
		return 0, fmt.Errorf("PORT must be between 1 and 65535, got %d", port)
	}
	return port, nil
}

// defaultAddr reads HOST and PORT, defaulting to the loopback and 5491.
func defaultAddr() (string, error) {
	host := os.Getenv("HOST")
	if host == "" {
		host = "127.0.0.1"
	}
	raw := os.Getenv("PORT")
	if raw == "" {
		raw = "5491"
	}
	port, err := parsePort(raw)
	if err != nil {
		return "", err
	}
	return net.JoinHostPort(host, strconv.Itoa(port)), nil
}
