package main

import (
	"encoding/binary"
	"errors"
	"hash/fnv"
)

const (
	defaultBucketSize = 4
	defaultMaxKicks   = 500
)

// Filter is a cuckoo filter over string keys with 16 bit fingerprints.
type Filter struct {
	buckets  [][]uint16
	size     int
	count    int
	maxKicks int
}

var errNoSpace = errors.New("cuckoo filter is full")

// New allocates a filter whose buckets hold roughly capacity entries.
func New(capacity int) *Filter {
	if capacity < 1 {
		capacity = 1
	}
	bucketCount := 1
	for bucketCount*defaultBucketSize < capacity {
		bucketCount <<= 1
	}
	return &Filter{
		buckets:  make([][]uint16, bucketCount),
		size:     bucketCount * defaultBucketSize,
		maxKicks: defaultMaxKicks,
	}
}

func hashOf(item string) uint64 {
	h := fnv.New64a()
	_, _ = h.Write([]byte(item))
	return h.Sum64()
}

func (f *Filter) fingerprint(item string) uint16 {
	fp := uint16(hashOf(item) >> 32)
	if fp == 0 {
		fp = 1
	}
	return fp
}

func (f *Filter) primaryIndex(item string) int {
	return int(hashOf(item) % uint64(len(f.buckets)))
}

func (f *Filter) alternateIndex(idx int, fp uint16) int {
	h := fnv.New64a()
	var buf [2]byte
	binary.LittleEndian.PutUint16(buf[:], fp)
	_, _ = h.Write(buf[:])
	return int((uint64(idx) ^ h.Sum64()) % uint64(len(f.buckets)))
}

// Insert adds item, evicting other fingerprints when both buckets are full.
func (f *Filter) Insert(item string) error {
	fp := f.fingerprint(item)
	i1 := f.primaryIndex(item)
	i2 := f.alternateIndex(i1, fp)
	for _, idx := range []int{i1, i2} {
		if len(f.buckets[idx]) < defaultBucketSize {
			f.buckets[idx] = append(f.buckets[idx], fp)
			f.count++
			return nil
		}
	}
	idx := i1
	for kick := 0; kick < f.maxKicks; kick++ {
		slot := int(hashOf(item+string(rune(kick))) % uint64(len(f.buckets[idx])))
		victim := f.buckets[idx][slot]
		f.buckets[idx][slot] = fp
		fp = victim
		idx = f.alternateIndex(idx, fp)
		if len(f.buckets[idx]) < defaultBucketSize {
			f.buckets[idx] = append(f.buckets[idx], fp)
			return nil
		}
	}
	return errNoSpace
}

// Lookup reports whether item may be present. False means definitely absent.
func (f *Filter) Lookup(item string) bool {
	fp := f.fingerprint(item)
	i1 := f.primaryIndex(item)
	i2 := f.alternateIndex(i1, fp)
	for _, idx := range []int{i1, i2} {
		for _, candidate := range f.buckets[idx] {
			if candidate == fp {
				return true
			}
		}
	}
	return false
}

// Delete removes one matching fingerprint and reports whether it found one.
func (f *Filter) Delete(item string) bool {
	fp := f.fingerprint(item)
	i1 := f.primaryIndex(item)
	i2 := f.alternateIndex(i1, fp)
	for _, idx := range []int{i1, i2} {
		for slot, candidate := range f.buckets[idx] {
			if candidate == fp {
				f.buckets[idx] = append(f.buckets[idx][:slot], f.buckets[idx][slot+1:]...)
				f.count--
				return true
			}
		}
	}
	return false
}

// Len returns the number of fingerprints inserted and not deleted.
func (f *Filter) Len() int { return f.count }
