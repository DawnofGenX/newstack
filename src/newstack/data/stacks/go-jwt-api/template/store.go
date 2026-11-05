package main

import (
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"sync"
)

// User is what the server keeps. The digest never leaves this package, and the
// API never renders this struct: a handler builds its own response type so a
// later field cannot leak by accident.
type User struct {
	ID      int    `json:"id"`
	Email   string `json:"email"`
	Digest  string `json:"digest"`
	Created string `json:"created"`
}

var ErrDuplicate = errors.New("email already registered")

// Store is a tiny user table with an optional JSON file behind it.
type Store struct {
	mu    sync.RWMutex
	users map[string]User // keyed by lower-cased email
	order []string
	path  string
}

func NewStore(path string) (*Store, error) {
	store := &Store{users: map[string]User{}, path: path}
	if path == "" {
		return store, nil
	}
	raw, err := os.ReadFile(path)
	if errors.Is(err, os.ErrNotExist) {
		return store, nil
	}
	if err != nil {
		return nil, err
	}
	var loaded []User
	if err := json.Unmarshal(raw, &loaded); err != nil {
		// A corrupt database must stop the process: starting empty would silently
		// forget every account and then overwrite the file on the next signup.
		return nil, err
	}
	for _, user := range loaded {
		key := normalise(user.Email)
		store.users[key] = user
		store.order = append(store.order, key)
	}
	return store, nil
}

func normalise(email string) string { return strings.ToLower(strings.TrimSpace(email)) }

// Add inserts a user, returning ErrDuplicate when the email is taken.
func (s *Store) Add(email, digest, created string) (User, error) {
	key := normalise(email)
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, taken := s.users[key]; taken {
		return User{}, ErrDuplicate
	}
	user := User{ID: len(s.order) + 1, Email: strings.TrimSpace(email), Digest: digest, Created: created}
	s.users[key] = user
	s.order = append(s.order, key)
	return user, nil
}

// Lookup returns the user and whether it exists.
func (s *Store) Lookup(email string) (User, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	user, ok := s.users[normalise(email)]
	return user, ok
}

// Count is how many accounts exist.
func (s *Store) Count() int {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return len(s.users)
}

// Save writes every user, atomically: a temp file in the same directory, then a
// rename. Writing in place would leave a truncated file if the process died
// mid-write, and the next start would refuse to boot.
func (s *Store) Save() error {
	if s.path == "" {
		return nil
	}
	s.mu.RLock()
	users := make([]User, 0, len(s.order))
	for _, key := range s.order {
		users = append(users, s.users[key])
	}
	s.mu.RUnlock()

	payload, err := json.MarshalIndent(users, "", "  ")
	if err != nil {
		return err
	}
	dir := filepath.Dir(s.path)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return err
	}
	temp, err := os.CreateTemp(dir, ".users-*.json")
	if err != nil {
		return err
	}
	name := temp.Name()
	if _, err := temp.Write(payload); err != nil {
		temp.Close()
		os.Remove(name)
		return err
	}
	if err := temp.Sync(); err != nil {
		temp.Close()
		os.Remove(name)
		return err
	}
	if err := temp.Close(); err != nil {
		os.Remove(name)
		return err
	}
	return os.Rename(name, s.path)
}
