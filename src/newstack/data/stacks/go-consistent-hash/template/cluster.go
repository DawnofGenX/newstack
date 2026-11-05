package main

import (
	"sort"
	"sync"
	"time"
)

// Cluster shards a KV cache across in-process nodes via the consistent hash
// ring, replicating each write to the first Replicas owners.
type Cluster struct {
	mu       sync.RWMutex
	Nodes    []*Node
	Ring     *Ring
	Replicas int
	clock    func() time.Time
}

// NewCluster builds a cluster with the named nodes and replica count.
func NewCluster(names []string, replicas int, clock func() time.Time) *Cluster {
	if replicas < 1 {
		replicas = 1
	}
	c := &Cluster{Ring: NewRing(), Replicas: replicas, clock: clock}
	for _, n := range names {
		c.addNodeLocked(n)
	}
	return c
}

func (c *Cluster) addNodeLocked(name string) *Node {
	for _, n := range c.Nodes {
		if n.Name == name {
			return n
		}
	}
	n := NewNode(name)
	if c.clock != nil {
		n.SetClock(c.clock)
	}
	c.Nodes = append(c.Nodes, n)
	sort.Slice(c.Nodes, func(i, j int) bool { return c.Nodes[i].Name < c.Nodes[j].Name })
	c.Ring.Add(name)
	return n
}

func (c *Cluster) nodeByName(name string) *Node {
	for _, n := range c.Nodes {
		if n.Name == name {
			return n
		}
	}
	return nil
}

// AddNode adds a node unless present; reports whether it was added.
func (c *Cluster) AddNode(name string) bool {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.nodeByName(name) != nil {
		return false
	}
	c.addNodeLocked(name)
	return true
}

// RemoveNode drops a node from the cluster; reports whether it existed.
func (c *Cluster) RemoveNode(name string) bool {
	c.mu.Lock()
	defer c.mu.Unlock()
	idx := -1
	for i, n := range c.Nodes {
		if n.Name == name {
			idx = i
			break
		}
	}
	if idx < 0 {
		return false
	}
	c.Nodes = append(c.Nodes[:idx], c.Nodes[idx+1:]...)
	c.Ring.Remove(name)
	return true
}

// Put writes to the first Replicas owners and returns them.
func (c *Cluster) Put(key, value string, ttl time.Duration) []string {
	c.mu.RLock()
	owners := c.Ring.Owners(key, c.Replicas)
	nodes := make([]*Node, 0, len(owners))
	for _, o := range owners {
		if n := c.nodeByName(o); n != nil {
			nodes = append(nodes, n)
		}
	}
	c.mu.RUnlock()
	for _, n := range nodes {
		n.Put(key, value, ttl)
	}
	return owners
}

// Get tries owners in ring order; returns value, serving node name, found.
func (c *Cluster) Get(key string) (string, string, bool) {
	c.mu.RLock()
	owners := c.Ring.Owners(key, len(c.Nodes))
	nodes := make([]*Node, 0, len(owners))
	for _, o := range owners {
		if n := c.nodeByName(o); n != nil {
			nodes = append(nodes, n)
		}
	}
	c.mu.RUnlock()
	for _, n := range nodes {
		if v, ok := n.Get(key); ok {
			return v, n.Name, true
		}
	}
	return "", "", false
}

// Delete removes key from every owner; reports whether any copy existed.
func (c *Cluster) Delete(key string) bool {
	c.mu.RLock()
	owners := c.Ring.Owners(key, len(c.Nodes))
	nodes := make([]*Node, 0, len(owners))
	for _, o := range owners {
		if n := c.nodeByName(o); n != nil {
			nodes = append(nodes, n)
		}
	}
	c.mu.RUnlock()
	found := false
	for _, n := range nodes {
		if n.Delete(key) {
			found = true
		}
	}
	return found
}

// Lens returns per-node live key counts.
func (c *Cluster) Lens() map[string]int {
	c.mu.RLock()
	defer c.mu.RUnlock()
	out := make(map[string]int, len(c.Nodes))
	for _, n := range c.Nodes {
		out[n.Name] = n.Len()
	}
	return out
}

// Health is the /health payload inputs: counts plus ring points.
func (c *Cluster) Health() (counts map[string]int, nodes int, points int) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	counts = make(map[string]int, len(c.Nodes))
	for _, n := range c.Nodes {
		counts[n.Name] = n.Len()
	}
	return counts, len(c.Nodes), c.Ring.Points()
}

// Owners exposes ring ownership for a key.
func (c *Cluster) Owners(key string) []string {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.Ring.Owners(key, c.Replicas)
}

// ReplicaCount is the configured replica fan-out.
func (c *Cluster) ReplicaCount() int { return c.Replicas }

// Rebalance moves every key owned by `to` (post-ring) that still sits on
// `from` (if still in the cluster) onto `to`, then strips it from `from`.
// Call after AddNode("to") so the ring already reflects the new placement.
func (c *Cluster) Rebalance(from, to string) int {
	c.mu.RLock()
	fromNode := c.nodeByName(from)
	toNode := c.nodeByName(to)
	ring := c.Ring
	replicas := c.Replicas
	c.mu.RUnlock()
	if toNode == nil {
		return 0
	}
	moved := 0
	if fromNode != nil {
		for _, kv := range fromNode.Snapshot() {
			owners := ring.Owners(kv[0], replicas)
			if len(owners) > 0 && owners[0] == to {
				toNode.Put(kv[0], kv[1], 0)
				fromNode.Delete(kv[0])
				moved++
			}
		}
	}
	// Strip keys that no longer belong on any remaining node's replica set:
	// for each surviving node, drop keys whose owner list excludes it.
	c.mu.RLock()
	nodes := append([]*Node(nil), c.Nodes...)
	c.mu.RUnlock()
	for _, n := range nodes {
		if n.Name == to {
			continue
		}
		for _, kv := range n.Snapshot() {
			owners := ring.Owners(kv[0], replicas)
			inList := false
			for _, o := range owners {
				if o == n.Name {
					inList = true
					break
				}
			}
			if !inList {
				n.Delete(kv[0])
			}
		}
	}
	return moved
}

// KeySet returns the union of live keys across nodes (tests/selftest).
func (c *Cluster) KeySet() []string {
	c.mu.RLock()
	nodes := append([]*Node(nil), c.Nodes...)
	c.mu.RUnlock()
	seen := map[string]bool{}
	for _, n := range nodes {
		for _, k := range n.store.Keys() {
			seen[k] = true
		}
	}
	out := make([]string, 0, len(seen))
	for k := range seen {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}
