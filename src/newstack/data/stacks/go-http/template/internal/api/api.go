// Package api exposes the HTTP handler for {{ npm_name }}.
package api

import (
	"encoding/json"
	"net/http"
	"sync"
)

// Item is a single stored record.
type Item struct {
	ID   int    `json:"id"`
	Name string `json:"name"`
}

// Store is an in-memory, concurrency-safe collection of items.
type Store struct {
	mu     sync.Mutex
	items  []Item
	nextID int
}

// NewStore returns an empty store.
func NewStore() *Store {
	return &Store{items: []Item{}, nextID: 1}
}

// List returns a snapshot copy of the stored items.
func (s *Store) List() []Item {
	s.mu.Lock()
	defer s.mu.Unlock()
	out := make([]Item, len(s.items))
	copy(out, s.items)
	return out
}

// Create appends an item and returns it with its assigned ID.
func (s *Store) Create(name string) Item {
	s.mu.Lock()
	defer s.mu.Unlock()
	item := Item{ID: s.nextID, Name: name}
	s.nextID++
	s.items = append(s.items, item)
	return item
}

// Handler returns an http.Handler wired to a fresh in-memory store.
func Handler() http.Handler {
	return handlerFor(NewStore())
}

func handlerFor(store *Store) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /health", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
	})
	mux.HandleFunc("GET /items", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, store.List())
	})
	mux.HandleFunc("POST /items", func(w http.ResponseWriter, r *http.Request) {
		var body struct {
			Name string `json:"name"`
		}
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid JSON body"})
			return
		}
		if body.Name == "" {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": "name is required"})
			return
		}
		writeJSON(w, http.StatusCreated, store.Create(body.Name))
	})
	return mux
}

func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(payload); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}
