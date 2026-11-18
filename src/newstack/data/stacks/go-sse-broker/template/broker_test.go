package main

import (
	"testing"
	"time"
)

func TestBrokerPubSub(t *testing.T) {
	b := NewBroker()
	ch := b.Subscribe()
	b.Publish("hello")
	select {
	case msg := <-ch:
		if msg != "hello" {
			t.Fatalf("got %s", msg)
		}
	case <-time.After(time.Second):
		t.Fatal("no message")
	}
	b.Unsubscribe(ch)
	if b.SubscriberCount() != 0 {
		t.Fatal("subscriber not removed")
	}
}

func TestBrokerFanOut(t *testing.T) {
	b := NewBroker()
	c1 := b.Subscribe()
	c2 := b.Subscribe()
	b.Publish("ping")
	for _, ch := range []chan string{c1, c2} {
		select {
		case msg := <-ch:
			if msg != "ping" {
				t.Fatalf("got %s", msg)
			}
		case <-time.After(time.Second):
			t.Fatal("missing fan-out")
		}
	}
	b.Unsubscribe(c1)
	b.Unsubscribe(c2)
}
