package app

import "testing"

func TestGreet(t *testing.T) {
	if got := Greet("smoke"); got != "Hello, smoke!" {
		t.Fatalf("got %q", got)
	}
	if got := Greet(""); got != "Hello, world!" {
		t.Fatalf("got %q", got)
	}
}

func TestAdd(t *testing.T) {
	if got := Add(4, 7); got != 11 {
		t.Fatalf("got %d", got)
	}
}