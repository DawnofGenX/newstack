package main

import (
	"fmt"
	"testing"
)

func TestInsertLookupHasNoFalseNegatives(t *testing.T) {
	f := New(128)
	var items []string
	for i := 0; i < 60; i++ {
		item := fmt.Sprintf("key-%d", i)
		items = append(items, item)
		if err := f.Insert(item); err != nil {
			t.Fatalf("insert %s: %v", item, err)
		}
	}
	for _, item := range items {
		if !f.Lookup(item) {
			t.Fatalf("false negative for %s", item)
		}
	}
	if f.Len() != len(items) {
		t.Fatalf("Len = %d, want %d", f.Len(), len(items))
	}
}

func TestDeleteRemovesItem(t *testing.T) {
	f := New(64)
	if err := f.Insert("alpha"); err != nil {
		t.Fatal(err)
	}
	if !f.Lookup("alpha") {
		t.Fatal("alpha should be present before delete")
	}
	if !f.Delete("alpha") {
		t.Fatal("delete reported no match")
	}
	if f.Lookup("alpha") {
		t.Fatal("alpha still present after delete")
	}
	if f.Delete("alpha") {
		t.Fatal("second delete should report no match")
	}
	if f.Len() != 0 {
		t.Fatalf("Len = %d, want 0", f.Len())
	}
}

func TestAbsentItemsAreUsuallyRejected(t *testing.T) {
	f := New(256)
	for i := 0; i < 20; i++ {
		if err := f.Insert(fmt.Sprintf("present-%d", i)); err != nil {
			t.Fatal(err)
		}
	}
	falsePositives := 0
	for i := 0; i < 200; i++ {
		if f.Lookup(fmt.Sprintf("absent-%d", i)) {
			falsePositives++
		}
	}
	if falsePositives > 20 {
		t.Fatalf("%d false positives out of 200 is too many", falsePositives)
	}
}

func TestFingerprintIsNeverZero(t *testing.T) {
	f := New(16)
	for i := 0; i < 100; i++ {
		if fp := f.fingerprint(fmt.Sprintf("item-%d", i)); fp == 0 {
			t.Fatal("fingerprint must not be zero")
		}
	}
}
