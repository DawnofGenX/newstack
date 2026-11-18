// Package main provides a fixed-size bitset with rank and select queries.
package main

import "math/bits"

// Bitmap is a set of non-negative integers packed into 64 bit words.
type Bitmap struct {
	words []uint64
}

// NewBitmap returns a bitmap with room for values below size.
func NewBitmap(size int) *Bitmap {
	if size < 0 {
		size = 0
	}
	return &Bitmap{words: make([]uint64, (size+63)/64)}
}

// Len is the number of addressable bits, rounded up to a word boundary.
func (b *Bitmap) Len() int { return len(b.words) * 64 }

// Set adds a value, reporting false when it is outside the bitmap.
func (b *Bitmap) Set(value int) bool {
	if value < 0 || value/64 >= len(b.words) {
		return false
	}
	b.words[value/64] |= 1 << uint(value%64)
	return true
}

// Clear removes a value; clearing an absent value is a no-op.
func (b *Bitmap) Clear(value int) {
	if value < 0 || value/64 >= len(b.words) {
		return
	}
	b.words[value/64] &^= 1 << uint(value%64)
}

// Has reports membership.
func (b *Bitmap) Has(value int) bool {
	if value < 0 || value/64 >= len(b.words) {
		return false
	}
	return b.words[value/64]&(1<<uint(value%64)) != 0
}

// Count is the number of set bits.
func (b *Bitmap) Count() int {
	total := 0
	for _, word := range b.words {
		total += bits.OnesCount64(word)
	}
	return total
}

// Rank counts set bits strictly below value.
func (b *Bitmap) Rank(value int) int {
	if value <= 0 {
		return 0
	}
	if value > b.Len() {
		value = b.Len()
	}
	total := 0
	full := value / 64
	for i := 0; i < full; i++ {
		total += bits.OnesCount64(b.words[i])
	}
	if rest := value % 64; rest > 0 && full < len(b.words) {
		mask := uint64(1)<<uint(rest) - 1
		total += bits.OnesCount64(b.words[full] & mask)
	}
	return total
}

// Select returns the index of the nth set bit (0 based), or -1 when absent.
func (b *Bitmap) Select(n int) int {
	if n < 0 {
		return -1
	}
	seen := 0
	for i, word := range b.words {
		if seen+bits.OnesCount64(word) <= n {
			seen += bits.OnesCount64(word)
			continue
		}
		for bit := 0; bit < 64; bit++ {
			if word&(1<<uint(bit)) == 0 {
				continue
			}
			if seen == n {
				return i*64 + bit
			}
			seen++
		}
	}
	return -1
}
