package main

import (
	"hash/fnv"
	"sort"
)

// VirtualNodesPerNode is the number of ring points each physical node owns.
const VirtualNodesPerNode = 150

// Hash is FNV-1a 64a plus an fmix64 finalizer. Raw FNV-1a has no avalanche
// past its last multiply, so sibling vnodes ("alpha#100".."alpha#109") land
// within ~2^33 of each other and one node swallows most of the key space;
// the mix spreads both vnode points and keys uniformly over uint64.
func Hash(s string) uint64 {
	h := fnv.New64a()
	_, _ = h.Write([]byte(s))
	x := h.Sum64()
	x ^= x >> 33
	x *= 0xff51afd7ed558ccd
	x ^= x >> 29
	x *= 0xc4ceb9fe1a85ec53
	x ^= x >> 32
	return x
}

// Ring is a consistent hash ring of sorted points, one owner per point.
type Ring struct {
	points []uint64
	owners []string
	nodes  map[string]bool
}

func NewRing() *Ring {
	return &Ring{nodes: map[string]bool{}}
}

// Clone returns an independent copy so callers can diff before/after state.
func (r *Ring) Clone() *Ring {
	c := &Ring{
		points: append([]uint64(nil), r.points...),
		owners: append([]string(nil), r.owners...),
		nodes:  map[string]bool{},
	}
	for n := range r.nodes {
		c.nodes[n] = true
	}
	return c
}

// Add inserts VirtualNodesPerNode points named "name#i" for the node.
func (r *Ring) Add(name string) {
	if r.nodes == nil {
		r.nodes = map[string]bool{}
	}
	r.nodes[name] = true
	for i := 0; i < VirtualNodesPerNode; i++ {
		p := Hash(vnodeName(name, i))
		idx := sort.Search(len(r.points), func(i int) bool { return r.points[i] >= p })
		r.points = append(r.points, 0)
		r.owners = append(r.owners, "")
		copy(r.points[idx+1:], r.points[idx:])
		copy(r.owners[idx+1:], r.owners[idx:])
		r.points[idx] = p
		r.owners[idx] = name
	}
}

// AddIfAbsent adds the node unless already present; reports whether it was added.
func (r *Ring) AddIfAbsent(name string) bool {
	if r.nodes[name] {
		return false
	}
	r.Add(name)
	return true
}

// Remove deletes every point belonging to name.
func (r *Ring) Remove(name string) {
	if !r.nodes[name] {
		return
	}
	delete(r.nodes, name)
	keep := make([]uint64, 0, len(r.points))
	keepOwners := make([]string, 0, len(r.owners))
	for i, o := range r.owners {
		if o != name {
			keep = append(keep, r.points[i])
			keepOwners = append(keepOwners, o)
		}
	}
	r.points = keep
	r.owners = keepOwners
}

func vnodeName(node string, i int) string {
	// node#i, hashed with FNV-1a 64a as required.
	buf := make([]byte, 0, len(node)+8)
	buf = append(buf, node...)
	buf = append(buf, '#')
	buf = appendInt(buf, i)
	return string(buf)
}

func appendInt(b []byte, i int) []byte {
	if i == 0 {
		return append(b, '0')
	}
	var digits [10]byte
	n := 0
	for i > 0 {
		digits[n] = byte('0' + i%10)
		i /= 10
		n++
	}
	for i := n - 1; i >= 0; i-- {
		b = append(b, digits[i])
	}
	return b
}

// Points returns the number of ring points.
func (r *Ring) Points() int { return len(r.points) }

// NodeCount returns the number of physical nodes.
func (r *Ring) NodeCount() int { return len(r.nodes) }

// Nodes returns sorted node names.
func (r *Ring) Nodes() []string {
	out := make([]string, 0, len(r.nodes))
	for n := range r.nodes {
		out = append(out, n)
	}
	sort.Strings(out)
	return out
}

// place returns the index of the first point >= h, wrapping to 0.
func (r *Ring) place(h uint64) int {
	if len(r.points) == 0 {
		return -1
	}
	idx := sort.Search(len(r.points), func(i int) bool { return r.points[i] >= h })
	if idx == len(r.points) {
		idx = 0
	}
	return idx
}

// Placement exposes the ring index a key lands on (test seam).
func (r *Ring) Placement(key string) int { return r.place(Hash(key)) }

// Owners returns up to replicas distinct node names starting at the first
// point >= hash(key) clockwise, wrapping to index 0.
func (r *Ring) Owners(key string, replicas int) []string {
	if len(r.points) == 0 || replicas <= 0 {
		return nil
	}
	if replicas > len(r.nodes) {
		replicas = len(r.nodes)
	}
	start := r.place(Hash(key))
	out := make([]string, 0, replicas)
	seen := make(map[string]bool, replicas)
	for i := 0; i < len(r.points) && len(out) < replicas; i++ {
		o := r.owners[(start+i)%len(r.points)]
		if !seen[o] {
			seen[o] = true
			out = append(out, o)
		}
	}
	return out
}

// Owner returns the primary owner of key.
func (r *Ring) Owner(key string) string {
	owners := r.Owners(key, 1)
	if len(owners) == 0 {
		return ""
	}
	return owners[0]
}

// Distribution counts keys per primary owner.
func (r *Ring) Distribution(keys []string) map[string]int {
	out := map[string]int{}
	for _, o := range r.Nodes() {
		out[o] = 0
	}
	for _, k := range keys {
		out[r.Owner(k)]++
	}
	return out
}

// OwnerShifts counts keys whose primary owner differs between two rings.
// Both rings must be non-empty.
func OwnerShifts(before, after *Ring, keys []string) int {
	shifted := 0
	for _, k := range keys {
		if before.Owner(k) != after.Owner(k) {
			shifted++
		}
	}
	return shifted
}
