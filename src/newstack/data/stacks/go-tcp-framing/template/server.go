package main

import (
	"bufio"
	"context"
	"errors"
	"net"
	"sync"
	"sync/atomic"
	"time"
)

// Server is a line-free TCP service: every message is a length-prefixed frame,
// and every connection is handled independently so one slow client cannot hold
// up another.
type Server struct {
	listener net.Listener
	idle     time.Duration
	wait     sync.WaitGroup
	mu       sync.Mutex
	conns    map[net.Conn]struct{}
	stopping atomic.Bool
}

// Listen binds the address. Call Serve to accept connections.
func Listen(addr string, idle time.Duration) (*Server, error) {
	listener, err := net.Listen("tcp", addr)
	if err != nil {
		return nil, err
	}
	return &Server{listener: listener, idle: idle, conns: map[net.Conn]struct{}{}}, nil
}

// Addr is the address actually bound, which matters when the caller asked for
// port 0.
func (s *Server) Addr() string {
	return s.listener.Addr().String()
}

// Serve accepts until the listener is closed.
func (s *Server) Serve() error {
	for {
		conn, err := s.listener.Accept()
		if err != nil {
			if s.stopping.Load() {
				return nil
			}
			return err
		}
		s.mu.Lock()
		s.conns[conn] = struct{}{}
		s.mu.Unlock()
		s.wait.Add(1)
		go s.handle(conn)
	}
}

// Shutdown stops accepting, then closes every open connection so a client
// parked in a read cannot keep the process alive.
func (s *Server) Shutdown(ctx context.Context) error {
	s.stopping.Store(true)
	err := s.listener.Close()
	s.mu.Lock()
	for conn := range s.conns {
		_ = conn.Close()
	}
	s.mu.Unlock()

	done := make(chan struct{})
	go func() {
		s.wait.Wait()
		close(done)
	}()
	select {
	case <-done:
	case <-ctx.Done():
		return ctx.Err()
	}
	return err
}

func (s *Server) handle(conn net.Conn) {
	defer s.wait.Done()
	defer func() {
		s.mu.Lock()
		delete(s.conns, conn)
		s.mu.Unlock()
		_ = conn.Close()
	}()

	reader := bufio.NewReader(conn)
	for {
		if s.idle > 0 {
			_ = conn.SetReadDeadline(time.Now().Add(s.idle))
		}
		payload, err := ReadFrame(reader, MaxFrame)
		if err != nil {
			// A framing mistake is answered once and then the connection is
			// closed: the stream is no longer aligned, so there is nothing
			// left to trust.
			if errors.Is(err, ErrEmptyFrame) {
				s.replyError(conn, "empty_frame", err.Error())
			} else if errors.Is(err, ErrFrameTooLarge) {
				s.replyError(conn, "frame_too_large", err.Error())
			}
			return
		}
		reply := Answer(payload)
		out, err := Encode(reply)
		if err != nil {
			return
		}
		if err := WriteFrame(conn, out); err != nil {
			return
		}
	}
}

func (s *Server) replyError(conn net.Conn, kind, detail string) {
	out, err := Encode(fail(kind, detail))
	if err != nil {
		return
	}
	_ = WriteFrame(conn, out)
}
