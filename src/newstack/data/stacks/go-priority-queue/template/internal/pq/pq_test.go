package pq

import "testing"

func TestBasicOrder(t *testing.T) {
	q := New()
	q.Push(2, "b")
	q.Push(1, "a")
	q.Push(3, "c")
	p, v, ok := q.Pop()
	if !ok || p != 1 || v != "a" {
		t.Fatalf("got %d %s %v", p, v, ok)
	}
}

func TestStableTieBreak(t *testing.T) {
	q := New()
	q.Push(1, "first")
	q.Push(1, "second")
	_, v1, _ := q.Pop()
	_, v2, _ := q.Pop()
	if v1 != "first" || v2 != "second" {
		t.Fatalf("order wrong: %s %s", v1, v2)
	}
}

func TestPeek(t *testing.T) {
	q := New()
	q.Push(5, "x")
	p, v, ok := q.Peek()
	if !ok || p != 5 || v != "x" {
		t.Fatalf("peek wrong: %d %s %v", p, v, ok)
	}
	if q.Len() != 1 {
		t.Fatalf("peek changed len")
	}
}
