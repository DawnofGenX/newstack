package main

import (
	"context"
	"errors"
	"log"
	"net"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"
)

// server wraps the mux plus a graceful stop, so main() stays about flags.
type server struct {
	http   *http.Server
	socket net.Listener
}

func newServer(addr string, h *handler) (*server, error) {
	listener, err := net.Listen("tcp", addr)
	if err != nil {
		return nil, err
	}
	mux := http.NewServeMux()
	mux.HandleFunc("/", h.route)
	// ReadHeaderTimeout bounds a client that opens a socket and never speaks; the
	// body reader has its own cap inside the handlers.
	httpServer := &http.Server{
		Handler:           mux,
		ReadHeaderTimeout: 5 * time.Second,
		IdleTimeout:       30 * time.Second,
	}
	return &server{http: httpServer, socket: listener}, nil
}

// Port is the bound port, which is not the requested one when addr used :0.
func (s *server) Port() int {
	if tcp, ok := s.socket.Addr().(*net.TCPAddr); ok {
		return tcp.Port
	}
	return 0
}

func (s *server) serve() error {
	err := s.http.Serve(s.socket)
	if errors.Is(err, http.ErrServerClosed) {
		return nil
	}
	return err
}

func (s *server) stop(ctx context.Context) error { return s.http.Shutdown(ctx) }

// listenAndServe is the production path: bind, serve, drain on SIGTERM.
func listenAndServe(addr string, h *handler) error {
	srv, err := newServer(addr, h)
	if err != nil {
		return err
	}
	done := make(chan error, 1)
	go func() { done <- srv.serve() }()

	signals := make(chan os.Signal, 1)
	signal.Notify(signals, syscall.SIGINT, syscall.SIGTERM)

	select {
	case err := <-done:
		return err
	case sig := <-signals:
		log.Printf("%s received: draining", sig)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	return srv.stop(ctx)
}

// envOr reads an environment variable with a fallback.
func envOr(name, fallback string) string {
	if value := os.Getenv(name); value != "" {
		return value
	}
	return fallback
}

// parsePort turns PORT into a number, refusing anything that is not a port.
func parsePort(raw string) (int, error) {
	port, err := strconv.Atoi(raw)
	if err != nil {
		return 0, err
	}
	if port < 1 || port > 65535 {
		return 0, errors.New("port out of range")
	}
	return port, nil
}
