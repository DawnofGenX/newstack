package main

import (
	"sort"
	"sync"
	"time"
)

// Store is a mutex-guarded KV map with TTL expiry evaluated on read.
type Store struct {
	mu    sync.RWMutex
	data  map[string]entry
	clock func() time.Time
	now   func() time.Time // injected clock, defaults to clock or time.Now
}

type entry struct {
	value     string
	expiresAt time.Time // zero means no expiry
}

// NewStore returns an empty store using time.Now unless a clock is injected.
func NewStore() *Store {
	return &Store{data: map[string]entry{}, now: time.Now}
}

// SetClock injects a clock function (tests). Nil keeps time.Now.
func (s *Store) SetClock(f func() time.Time) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if f != nil {
		s.now = f
	}
}

func (s *Store) clockNow() time.Time {
	if s.clock != nil {
		return s.clock()
	}
	if s.now != nil {
		return s.now()
	}
	return time.Now()
}

// Put stores key with an optional TTL (<=0 means no expiry).
func (s *Store) Put(key, value string, ttl time.Duration) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.data == nil {
		s.data = map[string]entry{}
	}
	e := entry{value: value}
	if ttl > 0 {
		e.expiresAt = s.clockNow().Add(ttl)
	}
	s.data[key] = e
}

// Get returns the value; expired keys are removed and reported missing.
func (s *Store) Get(key string) (string, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	e, ok := s.data[key]
	if !ok {
		return "", false
	}
	if !e.expiresAt.IsZero() && s.clockNow().After(e.expiresAt) {
		delete(s.data, key)
		return "", false
	}
	return e.value, true
}

// Delete removes key; reports whether it existed (expiry counts as absent).
func (s *Store) Delete(key string) bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	e, ok := s.data[key]
	if !ok {
		return false
	}
	if !e.expiresAt.IsZero() && s.clockNow().After(e.expiresAt) {
		delete(s.data, key)
		return false
	}
	delete(s.data, key)
	return true
}

// Len counts live (non-expired) keys.
func (s *Store) Len() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	now := s.clockNow()
	n := 0
	for k, e := range s.data {
		if !e.expiresAt.IsZero() && now.After(e.expiresAt) {
			delete(s.data, k)
			continue
		}
		n++
	}
	return n
}

// Keys returns sorted live keys.
func (s *Store) Keys() []string {
	s.mu.Lock()
	defer s.mu.Unlock()
	now := s.clockNow()
	out := make([]string, 0, len(s.data))
	for k, e := range s.data {
		if !e.expiresAt.IsZero() && now.After(e.expiresAt) {
			continue
		}
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}

// Snapshot returns sorted key/value pairs of live entries.
func (s *Store) Snapshot() [][2]string {
	s.mu.Lock()
	defer s.mu.Unlock()
	now := s.clockNow()
	out := make([][2]string, 0, len(s.data))
	for k, e := range s.data {
		if !e.expiresAt.IsZero() && now.After(e.expiresAt) {
			continue
		}
		out = append(out, [2]string{k, e.value})
	}
	sort.Slice(out, func(i, j int) bool { return out[i][0] < out[j][0] })
	return out
}
