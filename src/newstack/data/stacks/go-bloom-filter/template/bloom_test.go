package main

import (
	"fmt"
	"math/rand"
	"testing"
)

func TestAddCheck(t *testing.T) {
	bf := NewBloom(1024, 4)
	bf.Add("hello")
	if !bf.Check("hello") {
		t.Fatal("expected true")
	}
}

func TestFalsePositiveRate(t *testing.T) {
	bf := NewBloom(4096, 4)
	n := 200
	for i := 0; i < n; i++ {
		bf.Add(fmt.Sprintf("item-%d", i))
	}
	trials := 5000
	fp := 0
	rng := rand.New(rand.NewSource(42))
	for i := 0; i < trials; i++ {
		v := rng.Intn(1000000) + n + 1000
		if bf.Check(fmt.Sprintf("item-%d", v)) {
			fp++
		}
	}
	rate := float64(fp) / float64(trials)
	t.Logf("fp rate = %f", rate)
	if rate > 0.25 {
		t.Fatalf("fp rate too high: %f", rate)
	}
}

func TestStats(t *testing.T) {
	bf := NewBloom(64, 2)
	bf.Add("a")
	if bf.Stats() == "" {
		t.Fatal("empty stats")
	}
}
