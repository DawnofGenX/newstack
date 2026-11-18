package main

import "testing"

func build(values ...int) *Bitmap {
	bitmap := NewBitmap(256)
	for _, value := range values {
		bitmap.Set(value)
	}
	return bitmap
}

func TestSetAndHas(t *testing.T) {
	bitmap := build(1, 63, 64, 200)
	for _, value := range []int{1, 63, 64, 200} {
		if !bitmap.Has(value) {
			t.Fatalf("Has(%d) = false, want true", value)
		}
	}
	for _, value := range []int{0, 2, 255} {
		if bitmap.Has(value) {
			t.Fatalf("Has(%d) = true, want false", value)
		}
	}
}

func TestSetOutsideRangeFails(t *testing.T) {
	bitmap := NewBitmap(64)
	if bitmap.Set(64) {
		t.Fatal("Set(64) should fail on a 64 bit bitmap")
	}
	if bitmap.Set(-1) {
		t.Fatal("Set(-1) should fail")
	}
}

func TestClear(t *testing.T) {
	bitmap := build(5)
	bitmap.Clear(5)
	if bitmap.Has(5) {
		t.Fatal("value survived Clear")
	}
	bitmap.Clear(5)
	if bitmap.Count() != 0 {
		t.Fatalf("Count() = %d, want 0", bitmap.Count())
	}
}

func TestCountAndRank(t *testing.T) {
	bitmap := build(0, 3, 64, 65)
	if got := bitmap.Count(); got != 4 {
		t.Fatalf("Count() = %d, want 4", got)
	}
	type rankCase struct{ value, want int }
	cases := []rankCase{
		{0, 0},
		{1, 1},
		{64, 2},
		{65, 3},
		{66, 4},
		{1000, 4},
	}
	for _, c := range cases {
		if got := bitmap.Rank(c.value); got != c.want {
			t.Fatalf("Rank(%d) = %d, want %d", c.value, got, c.want)
		}
	}
}

func TestSelect(t *testing.T) {
	bitmap := build(0, 3, 64, 65)
	want := []int{0, 3, 64, 65}
	for index, value := range want {
		if got := bitmap.Select(index); got != value {
			t.Fatalf("Select(%d) = %d, want %d", index, got, value)
		}
	}
	if got := bitmap.Select(4); got != -1 {
		t.Fatalf("Select(4) = %d, want -1", got)
	}
}

func TestRankAndSelectAreInverse(t *testing.T) {
	bitmap := build(2, 9, 70, 71, 100)
	for index := 0; index < bitmap.Count(); index++ {
		value := bitmap.Select(index)
		if got := bitmap.Rank(value); got != index {
			t.Fatalf("Rank(Select(%d)) = %d", index, got)
		}
	}
}
