package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"sync"
)

type Event struct {
	ID      int             `json:"id"`
	Payload json.RawMessage `json:"payload"`
}

type Server struct {
	mu     sync.Mutex
	events []Event
	nextID int
}

func NewServer() *Server {
	return &Server{nextID: 1}
}

func (s *Server) Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"status":"ok"}`))
	})
	mux.HandleFunc("/webhook", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		var payload json.RawMessage
		if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
			http.Error(w, "bad json", http.StatusBadRequest)
			return
		}
		s.mu.Lock()
		ev := Event{ID: s.nextID, Payload: payload}
		s.nextID++
		s.events = append(s.events, ev)
		s.mu.Unlock()
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		json.NewEncoder(w).Encode(ev)
	})
	mux.HandleFunc("/events", func(w http.ResponseWriter, r *http.Request) {
		s.mu.Lock()
		out := append([]Event(nil), s.events...)
		s.mu.Unlock()
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(out)
	})
	return mux
}

func (s *Server) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	s.Handler().ServeHTTP(w, r)
}

func Run(addr string) error {
	srv := &http.Server{Addr: addr, Handler: NewServer().Handler()}
	log.Printf("listening on %s", addr)
	return srv.ListenAndServe()
}

func main() {
	port := flag.String("port", envOr("PORT", "5592"), "listen port")
	flag.Parse()
	addr := ":" + *port
	if err := Run(addr); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
