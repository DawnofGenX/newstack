package cache

import (
	"testing"
	"time"
)

func TestLRUEviction(t *testing.T) {
	c := New[string, int](2, 0)
	c.Put("a", 1)
	c.Put("b", 2)
	c.Put("c", 3)
	if _, ok := c.Get("a"); ok {
		t.Fatal("a should be evicted")
	}
	if v, ok := c.Get("b"); !ok || v != 2 {
		t.Fatalf("b missing: %v %v", v, ok)
	}
}

func TestTTL(t *testing.T) {
	c := New[string, int](2, 10*time.Millisecond)
	c.Put("a", 1)
	time.Sleep(20 * time.Millisecond)
	if _, ok := c.Get("a"); ok {
		t.Fatal("a should be expired")
	}
	hits, misses := c.Stats()
	if hits != 0 || misses != 1 {
		t.Fatalf("stats wrong: %d %d", hits, misses)
	}
}

func TestHitMiss(t *testing.T) {
	c := New[string, int](2, 0)
	c.Put("a", 1)
	c.Get("a")
	c.Get("z")
	hits, misses := c.Stats()
	if hits != 1 || misses != 1 {
		t.Fatalf("stats wrong: %d %d", hits, misses)
	}
}
