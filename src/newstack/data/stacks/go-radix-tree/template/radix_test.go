package main

import (
	"reflect"
	"testing"
)

func seed(t *testing.T) *Tree {
	t.Helper()
	tree := New()
	for _, kv := range [][2]string{
		{"romane", "1"},
		{"romanus", "2"},
		{"romulus", "3"},
		{"rubens", "4"},
		{"ruber", "5"},
		{"rubicon", "6"},
		{"rubicundus", "7"},
	} {
		tree.Insert(kv[0], kv[1])
	}
	return tree
}

func TestInsertAndGet(t *testing.T) {
	tree := seed(t)
	for key, want := range map[string]string{
		"romane": "1", "romanus": "2", "romulus": "3", "rubens": "4",
		"ruber": "5", "rubicon": "6", "rubicundus": "7",
	} {
		got, ok := tree.Get(key)
		if !ok || got != want {
			t.Fatalf("Get(%q) = %q, %v; want %q", key, got, ok, want)
		}
	}
	for _, missing := range []string{"rom", "romanes", "rub", "x"} {
		if _, ok := tree.Get(missing); ok {
			t.Fatalf("Get(%q) unexpectedly found a value", missing)
		}
	}
}

func TestOverwriteValue(t *testing.T) {
	tree := New()
	tree.Insert("alpha", "one")
	tree.Insert("alpha", "two")
	if got, _ := tree.Get("alpha"); got != "two" {
		t.Fatalf("Get = %q, want two", got)
	}
	if tree.Len() != 1 {
		t.Fatalf("Len = %d, want 1", tree.Len())
	}
}

func TestLongestPrefix(t *testing.T) {
	tree := seed(t)
	cases := []struct {
		input   string
		wantKey string
		wantVal string
		found   bool
	}{
		{"romanus", "romanus", "2", true},
		{"romanesque", "romane", "1", true},
		{"rubicundusly", "rubicundus", "7", true},
		{"ruberic", "ruber", "5", true},
		{"zulu", "", "", false},
	}
	for _, tc := range cases {
		key, value, ok := tree.LongestPrefix(tc.input)
		if ok != tc.found || key != tc.wantKey || value != tc.wantVal {
			t.Fatalf("LongestPrefix(%q) = %q %q %v; want %q %q %v", tc.input, key, value, ok, tc.wantKey, tc.wantVal, tc.found)
		}
	}
}

func TestKeysAreSortedAndComplete(t *testing.T) {
	tree := seed(t)
	want := []string{"romane", "romanus", "romulus", "rubens", "ruber", "rubicon", "rubicundus"}
	if got := tree.Keys(); !reflect.DeepEqual(got, want) {
		t.Fatalf("Keys = %v, want %v", got, want)
	}
	if tree.Len() != len(want) {
		t.Fatalf("Len = %d, want %d", tree.Len(), len(want))
	}
}

func TestEmptyKeyIsStorable(t *testing.T) {
	tree := New()
	tree.Insert("", "root")
	if got, ok := tree.Get(""); !ok || got != "root" {
		t.Fatalf("Get(empty) = %q, %v", got, ok)
	}
	if _, value, ok := tree.LongestPrefix("anything"); !ok || value != "root" {
		t.Fatalf("LongestPrefix should fall back to the empty key")
	}
}
