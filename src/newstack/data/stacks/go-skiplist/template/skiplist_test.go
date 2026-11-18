package main

import (
	"strings"
	"testing"
)

func TestSkipListBasic(t *testing.T) {
	sl := NewSkipList()
	for _, v := range []string{"banana", "apple", "cherry"} {
		if !sl.Insert(v) {
			t.Fatalf("insert failed %s", v)
		}
	}
	if sl.Len() != 3 {
		t.Fatalf("len %d", sl.Len())
	}
	if !sl.Contains("apple") {
		t.Fatal("missing apple")
	}
	if sl.Contains("grape") {
		t.Fatal("unexpected grape")
	}
	if !sl.Delete("apple") {
		t.Fatal("delete failed")
	}
	if sl.Contains("apple") {
		t.Fatal("apple still present")
	}
	if sl.Len() != 2 {
		t.Fatalf("len %d", sl.Len())
	}
	_ = strings.NewReader
}
