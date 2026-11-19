package main

import "testing"

func TestTopKBasic(t *testing.T) {
	res := TopK([]float64{5, 1, 9, 2, 8}, 3)
	if len(res) != 3 || res[0] != 9 || res[1] != 8 || res[2] != 5 {
		t.Fatalf("got %v", res)
	}
}

func TestTopKAll(t *testing.T) {
	res := TopK([]float64{3, 1, 2}, 5)
	if len(res) != 3 {
		t.Fatalf("got %v", res)
	}
}

func TestTopKZero(t *testing.T) {
	res := TopK([]float64{1, 2, 3}, 0)
	if len(res) != 0 {
		t.Fatalf("got %v", res)
	}
}