package cmap

import (
	"sync"
	"testing"
)

func TestBasic(t *testing.T) {
	m := New[string, int]()
	m.Set("a", 1)
	v, ok := m.Get("a")
	if !ok || v != 1 {
		t.Fatalf("got %v %v", v, ok)
	}
	m.Delete("a")
	if _, ok := m.Get("a"); ok {
		t.Fatal("expected missing")
	}
	if m.Len() != 0 {
		t.Fatalf("len %d", m.Len())
	}
}

func TestConcurrent(t *testing.T) {
	m := New[int, int]()
	var wg sync.WaitGroup
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func(base int) {
			defer wg.Done()
			for j := 0; j < 1000; j++ {
				key := base*1000 + j
				m.Set(key, key)
			}
		}(i)
	}
	wg.Wait()
	if m.Len() != 8000 {
		t.Fatalf("len %d", m.Len())
	}
}

func TestRange(t *testing.T) {
	m := New[string, int]()
	m.Set("a", 1)
	m.Set("b", 2)
	count := 0
	m.Range(func(k string, v int) bool {
		count++
		return true
	})
	if count != 2 {
		t.Fatalf("count %d", count)
	}
}

func BenchmarkSetGet(b *testing.B) {
	m := New[int, int]()
	b.RunParallel(func(pb *testing.PB) {
		i := 0
		for pb.Next() {
			m.Set(i, i)
			m.Get(i)
			i++
		}
	})
}
