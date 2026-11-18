package main

import "sort"

type node struct {
	prefix   string
	value    string
	hasValue bool
	children map[byte]*node
}

func newNode(prefix string) *node {
	return &node{prefix: prefix, children: make(map[byte]*node)}
}

// Tree is a radix tree (compressed trie) over byte keys.
type Tree struct {
	root *node
}

// New returns an empty tree.
func New() *Tree {
	return &Tree{root: newNode("")}
}

func commonPrefixLen(a, b string) int {
	n := 0
	for n < len(a) && n < len(b) && a[n] == b[n] {
		n++
	}
	return n
}

// Insert stores value under key, replacing any previous value.
func (t *Tree) Insert(key, value string) {
	cur := t.root
	rest := key
	for {
		if rest == "" {
			cur.value = value
			cur.hasValue = true
			return
		}
		child, ok := cur.children[rest[0]]
		if !ok {
			leaf := newNode(rest)
			leaf.value = value
			leaf.hasValue = true
			cur.children[rest[0]] = leaf
			return
		}
		n := commonPrefixLen(child.prefix, rest)
		if n == len(child.prefix) {
			cur = child
			rest = rest[n:]
			continue
		}
		// split the edge at the divergence point
		mid := newNode(child.prefix[:n])
		child.prefix = child.prefix[n:]
		mid.children[child.prefix[0]] = child
		cur.children[rest[0]] = mid
		if n == len(rest) {
			mid.value = value
			mid.hasValue = true
			return
		}
		leaf := newNode(rest[n:])
		leaf.value = value
		leaf.hasValue = true
		mid.children[leaf.prefix[0]] = leaf
		return
	}
}

// Get returns the value stored under key.
func (t *Tree) Get(key string) (string, bool) {
	cur := t.root
	rest := key
	for {
		if rest == "" {
			return cur.value, cur.hasValue
		}
		child, ok := cur.children[rest[0]]
		if !ok {
			return "", false
		}
		if len(rest) < len(child.prefix) || child.prefix != rest[:len(child.prefix)] {
			return "", false
		}
		cur = child
		rest = rest[len(child.prefix):]
	}
}

// LongestPrefix returns the longest stored key that prefixes input.
func (t *Tree) LongestPrefix(input string) (string, string, bool) {
	cur := t.root
	rest := input
	bestKey, bestValue := "", ""
	found := false
	if cur.hasValue {
		bestKey, bestValue, found = "", cur.value, true
	}
	for rest != "" {
		child, ok := cur.children[rest[0]]
		if !ok {
			break
		}
		if len(rest) < len(child.prefix) || child.prefix != rest[:len(child.prefix)] {
			break
		}
		if child.hasValue {
			bestKey = input[:len(input)-len(rest)+len(child.prefix)]
			bestValue = child.value
			found = true
		}
		cur = child
		rest = rest[len(child.prefix):]
	}
	return bestKey, bestValue, found
}

// Keys returns every stored key in lexicographic order.
func (t *Tree) Keys() []string {
	var out []string
	var walk func(n *node, prefix string)
	walk = func(n *node, prefix string) {
		full := prefix + n.prefix
		if n.hasValue {
			out = append(out, full)
		}
		labels := make([]byte, 0, len(n.children))
		for label := range n.children {
			labels = append(labels, label)
		}
		sort.Slice(labels, func(i, j int) bool { return labels[i] < labels[j] })
		for _, label := range labels {
			walk(n.children[label], full)
		}
	}
	walk(t.root, "")
	return out
}

// Len reports how many keys are stored.
func (t *Tree) Len() int { return len(t.Keys()) }
