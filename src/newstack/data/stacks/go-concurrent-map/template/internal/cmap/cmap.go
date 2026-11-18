package cmap

import (
	"fmt"
	"hash/fnv"
	"sync"
)

const defaultShards = 32

type shard[K comparable, V any] struct {
	mu sync.RWMutex
	m  map[K]V
}

type Map[K comparable, V any] struct {
	shards []*shard[K, V]
}

func New[K comparable, V any]() *Map[K, V] {
	return NewWithShards[K, V](defaultShards)
}

func NewWithShards[K comparable, V any](n int) *Map[K, V] {
	if n < 1 {
		n = 1
	}
	m := &Map[K, V]{shards: make([]*shard[K, V], n)}
	for i := range m.shards {
		m.shards[i] = &shard[K, V]{m: make(map[K]V)}
	}
	return m
}

func (m *Map[K, V]) shardFor(key K) *shard[K, V] {
	h := fnv.New64a()
	fmt.Fprint(h, key)
	return m.shards[h.Sum64()%uint64(len(m.shards))]
}

func (m *Map[K, V]) Set(key K, value V) {
	s := m.shardFor(key)
	s.mu.Lock()
	defer s.mu.Unlock()
	s.m[key] = value
}

func (m *Map[K, V]) Get(key K) (V, bool) {
	s := m.shardFor(key)
	s.mu.RLock()
	defer s.mu.RUnlock()
	v, ok := s.m[key]
	return v, ok
}

func (m *Map[K, V]) Delete(key K) {
	s := m.shardFor(key)
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.m, key)
}

func (m *Map[K, V]) Len() int {
	n := 0
	for _, s := range m.shards {
		s.mu.RLock()
		n += len(s.m)
		s.mu.RUnlock()
	}
	return n
}

// Range calls fn for each key/value. If fn returns false, iteration stops.
func (m *Map[K, V]) Range(fn func(K, V) bool) {
	for _, s := range m.shards {
		s.mu.RLock()
		for k, v := range s.m {
			if !fn(k, v) {
				s.mu.RUnlock()
				return
			}
		}
		s.mu.RUnlock()
	}
}
