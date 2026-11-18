package main

import (
	"sync"
	"time"
)

type bucket struct {
	tokens float64
	last   time.Time
}

type bucketStore struct {
	mu      sync.Mutex
	rate    float64
	burst   int
	buckets map[string]*bucket
}

func newBucketStore(rate float64, burst int) *bucketStore {
	return &bucketStore{rate: rate, burst: burst, buckets: make(map[string]*bucket)}
}

func (s *bucketStore) allow(key string) bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	b, ok := s.buckets[key]
	now := time.Now()
	if !ok {
		b = &bucket{tokens: float64(s.burst), last: now}
		s.buckets[key] = b
	}
	elapsed := now.Sub(b.last).Seconds()
	b.tokens += elapsed * s.rate
	if b.tokens > float64(s.burst) {
		b.tokens = float64(s.burst)
	}
	b.last = now
	if b.tokens < 1 {
		return false
	}
	b.tokens -= 1
	return true
}
