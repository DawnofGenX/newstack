package main

import (
	"flag"
	"fmt"
	"os"
	"time"
)

type State int

const (
	Closed State = iota
	Open
	HalfOpen
)

func (s State) String() string {
	switch s {
	case Closed:
		return "closed"
	case Open:
		return "open"
	case HalfOpen:
		return "half-open"
	}
	return "unknown"
}

type Clock interface {
	Now() time.Time
}

type RealClock struct{}

func (RealClock) Now() time.Time { return time.Now() }

type fakeClock struct {
	now time.Time
}

func (f *fakeClock) Now() time.Time { return f.now }

func (f *fakeClock) advance(d time.Duration) { f.now = f.now.Add(d) }

type CircuitBreaker struct {
	threshold int
	cooldown  time.Duration
	clock     Clock

	state        State
	failures     int
	openedAt     time.Time
	halfOpenUsed bool
}

func NewCircuitBreaker(threshold int, cooldown time.Duration, clock Clock) *CircuitBreaker {
	if clock == nil {
		clock = RealClock{}
	}
	return &CircuitBreaker{threshold: threshold, cooldown: cooldown, clock: clock, state: Closed}
}

func (cb *CircuitBreaker) State() State {
	cb.transition()
	return cb.state
}

func (cb *CircuitBreaker) transition() {
	if cb.state == Open {
		if cb.clock.Now().Sub(cb.openedAt) >= cb.cooldown {
			cb.state = HalfOpen
			cb.halfOpenUsed = false
		}
	}
}

func (cb *CircuitBreaker) Allow() bool {
	cb.transition()
	switch cb.state {
	case Closed:
		return true
	case Open:
		return false
	case HalfOpen:
		if cb.halfOpenUsed {
			return false
		}
		cb.halfOpenUsed = true
		return true
	}
	return false
}

func (cb *CircuitBreaker) RecordSuccess() {
	cb.transition()
	switch cb.state {
	case HalfOpen:
		cb.state = Closed
		cb.failures = 0
	case Closed:
		cb.failures = 0
	}
}

func (cb *CircuitBreaker) RecordFailure() {
	cb.transition()
	switch cb.state {
	case Closed:
		cb.failures++
		if cb.failures >= cb.threshold {
			cb.state = Open
			cb.openedAt = cb.clock.Now()
		}
	case HalfOpen:
		cb.state = Open
		cb.openedAt = cb.clock.Now()
		cb.halfOpenUsed = true
	case Open:
		cb.openedAt = cb.clock.Now()
	}
}

func (cb *CircuitBreaker) Failures() int { return cb.failures }

func main() {
	threshold := flag.Int("threshold", 3, "failure threshold")
	cooldown := flag.Duration("cooldown", 10*time.Second, "cooldown")
	demo := flag.Bool("demo", false, "run deterministic demo")
	flag.Parse()

	if *demo {
		clock := &fakeClock{now: time.Unix(0, 0)}
		cb := NewCircuitBreaker(*threshold, *cooldown, clock)
		steps := []func(){
			func() { cb.RecordFailure(); fmt.Println("fail ->", cb.State()) },
			func() { cb.RecordFailure(); fmt.Println("fail ->", cb.State()) },
			func() { cb.RecordFailure(); fmt.Println("fail ->", cb.State()) },
			func() { clock.advance(*cooldown); fmt.Println("advance ->", cb.State()) },
			func() { cb.Allow(); fmt.Println("allow probe ->", cb.State()) },
			func() { cb.RecordSuccess(); fmt.Println("success ->", cb.State()) },
		}
		for _, s := range steps {
			s()
		}
		return
	}
	_ = os.Args
	fmt.Println("use --demo")
}
