package main

import (
	"sync"
	"time"
)

// Node is one physical cache node wrapping a Store.
type Node struct {
	Name  string
	store *Store
	mu    sync.Mutex
}

// NewNode builds a node with an empty store.
func NewNode(name string) *Node {
	return &Node{Name: name, store: NewStore()}
}

// SetClock forwards the injected clock to the underlying store.
func (n *Node) SetClock(f func() time.Time) {
	n.mu.Lock()
	defer n.mu.Unlock()
	n.store.SetClock(f)
}

func (n *Node) Put(key, value string, ttl time.Duration) {
	n.mu.Lock()
	defer n.mu.Unlock()
	n.store.Put(key, value, ttl)
}

func (n *Node) Get(key string) (string, bool) {
	n.mu.Lock()
	defer n.mu.Unlock()
	return n.store.Get(key)
}

func (n *Node) Delete(key string) bool {
	n.mu.Lock()
	defer n.mu.Unlock()
	return n.store.Delete(key)
}

func (n *Node) Len() int {
	n.mu.Lock()
	defer n.mu.Unlock()
	return n.store.Len()
}

// Snapshot exposes the node's live pairs (for Rebalance transfers).
func (n *Node) Snapshot() [][2]string {
	n.mu.Lock()
	defer n.mu.Unlock()
	return n.store.Snapshot()
}
