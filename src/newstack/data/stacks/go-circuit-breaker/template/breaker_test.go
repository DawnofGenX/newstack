package main

import (
	"testing"
	"time"
)

func TestClosedToOpen(t *testing.T) {
	clock := &fakeClock{now: time.Unix(0, 0)}
	cb := NewCircuitBreaker(2, time.Second, clock)
	cb.RecordFailure()
	cb.RecordFailure()
	if cb.State() != Open {
		t.Fatalf("expected open, got %s", cb.State())
	}
}

func TestCooldownHalfOpen(t *testing.T) {
	clock := &fakeClock{now: time.Unix(0, 0)}
	cb := NewCircuitBreaker(1, time.Second, clock)
	cb.RecordFailure()
	if cb.State() != Open {
		t.Fatal("expected open")
	}
	clock.advance(time.Second)
	if cb.State() != HalfOpen {
		t.Fatalf("expected half-open, got %s", cb.State())
	}
}

func TestHalfOpenSuccessCloses(t *testing.T) {
	clock := &fakeClock{now: time.Unix(0, 0)}
	cb := NewCircuitBreaker(1, time.Second, clock)
	cb.RecordFailure()
	clock.advance(time.Second)
	if !cb.Allow() {
		t.Fatal("probe should be allowed")
	}
	cb.RecordSuccess()
	if cb.State() != Closed {
		t.Fatalf("expected closed, got %s", cb.State())
	}
}

func TestHalfOpenFailureReopens(t *testing.T) {
	clock := &fakeClock{now: time.Unix(0, 0)}
	cb := NewCircuitBreaker(1, time.Second, clock)
	cb.RecordFailure()
	clock.advance(time.Second)
	cb.Allow()
	cb.RecordFailure()
	if cb.State() != Open {
		t.Fatalf("expected open, got %s", cb.State())
	}
}

func TestAllowInClosed(t *testing.T) {
	cb := NewCircuitBreaker(3, time.Second, nil)
	if !cb.Allow() {
		t.Fatal("closed should allow")
	}
}
