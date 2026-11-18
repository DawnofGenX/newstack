package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestWebhookReceiveAndList(t *testing.T) {
	srv := NewServer()
	ts := httptest.NewServer(srv.Handler())
	defer ts.Close()

	resp, err := http.Post(ts.URL+"/webhook", "application/json", bytes.NewBufferString(`{"msg":"hi"}`))
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusCreated {
		t.Fatalf("status %d", resp.StatusCode)
	}

	r2, err := http.Get(ts.URL + "/events")
	if err != nil {
		t.Fatal(err)
	}
	defer r2.Body.Close()
	var events []Event
	if err := json.NewDecoder(r2.Body).Decode(&events); err != nil {
		t.Fatal(err)
	}
	if len(events) != 1 {
		t.Fatalf("events %d", len(events))
	}
	if !strings.Contains(string(events[0].Payload), "hi") {
		t.Fatalf("payload %s", events[0].Payload)
	}

	r3, err := http.Get(ts.URL + "/health")
	if err != nil {
		t.Fatal(err)
	}
	defer r3.Body.Close()
	if r3.StatusCode != http.StatusOK {
		t.Fatalf("health %d", r3.StatusCode)
	}
}
