package main

import "testing"

func TestHaversineZero(t *testing.T) {
	if d := Haversine(0, 0, 0, 0); d != 0 {
		t.Fatalf("expected 0, got %v", d)
	}
}

func TestHaversineNYLondon(t *testing.T) {
	d := Haversine(40.7128, -74.006, 51.5074, -0.1278)
	if d < 5560 || d > 5580 {
		t.Fatalf("expected ~5570, got %v", d)
	}
}