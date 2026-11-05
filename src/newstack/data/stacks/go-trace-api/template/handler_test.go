package main

import (
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func startService(t *testing.T, limit int) (*httptest.Server, *Tracker) {
	t.Helper()
	tracker := NewTracker(NewRecorder(limit))
	server := httptest.NewServer(newHandler(tracker))
	t.Cleanup(server.Close)
	return server, tracker
}

func get(t *testing.T, url string, header map[string]string) (*http.Response, string) {
	t.Helper()
	request, err := http.NewRequest("GET", url, nil)
	if err != nil {
		t.Fatal(err)
	}
	for key, value := range header {
		request.Header.Set(key, value)
	}
	response, err := http.DefaultClient.Do(request)
	if err != nil {
		t.Fatal(err)
	}
	defer response.Body.Close()
	body, err := io.ReadAll(response.Body)
	if err != nil {
		t.Fatal(err)
	}
	return response, string(body)
}

func TestStatsLinksTheChildSpanToTheCaller(t *testing.T) {
	server, _ := startService(t, 32)
	const incoming = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"

	response, body := get(t, server.URL+"/stats?text=h%C3%A9llo+w%C3%B6rld%0A", map[string]string{"traceparent": incoming})
	if response.StatusCode != 200 {
		t.Fatalf("status %d: %s", response.StatusCode, body)
	}
	if body != `{"text":"héllo wörld\n","lines":1,"words":2,"bytes":14}` {
		t.Fatalf("unexpected body: %s", body)
	}
	announced, err := ParseTraceparent(response.Header.Get("traceparent"))
	if err != nil {
		t.Fatalf("the response header must parse: %v", err)
	}
	if announced.TraceID != "4bf92f3577b34da6a3ce929d0e0e4736" {
		t.Fatalf("the response must keep the trace: %s", announced.String())
	}
	if announced.SpanID == "00f067aa0ba902b7" {
		t.Fatal("the response must announce the span that served it, not the caller's")
	}

	_, spansBody := get(t, server.URL+"/spans", nil)
	var list spanList
	if err := json.Unmarshal([]byte(spansBody), &list); err != nil {
		t.Fatal(err)
	}
	var request, child *Span
	for i := range list.Spans {
		switch list.Spans[i].Name {
		case "stats":
			request = &list.Spans[i]
		case "count":
			child = &list.Spans[i]
		}
	}
	if request == nil || child == nil {
		t.Fatalf("both spans must be exported: %s", spansBody)
	}
	if request.ParentID != "00f067aa0ba902b7" {
		t.Fatalf("the request span must point at the caller: %+v", request)
	}
	if child.ParentID != request.SpanID {
		t.Fatalf("the child must point at the request span: %+v", child)
	}
}

func TestUnsampledTracesAreNotStored(t *testing.T) {
	server, tracker := startService(t, 32)
	_, _ = get(t, server.URL+"/stats?text=one", map[string]string{
		"traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-00",
	})
	if stored := tracker.recorder.Count(); stored != 0 {
		t.Fatalf("an unsampled trace stored %d spans", stored)
	}
}

func TestErrorsSpeakInJSON(t *testing.T) {
	server, _ := startService(t, 32)

	cases := []struct {
		method string
		path   string
		body   string
		header map[string]string
		status int
		needle string
	}{
		{"GET", "/nope", "", nil, 404, `"error":"not_found"`},
		{"PUT", "/health", "", nil, 405, `"error":"method_not_allowed"`},
		{"POST", "/stats", `{}`, nil, 422, `"error":"missing_text"`},
		{"POST", "/stats", `{"text":42}`, nil, 422, `"error":"missing_text"`},
		{"POST", "/stats", `oops`, nil, 422, `"error":"invalid_json"`},
		{"GET", "/stats", "", map[string]string{"traceparent": "00-xyz"}, 400, `"error":"invalid_traceparent"`},
		{"GET", "/spans?trace=zzz", "", nil, 400, `"error":"invalid_trace"`},
	}
	for _, item := range cases {
		request, err := http.NewRequest(item.method, server.URL+item.path, strings.NewReader(item.body))
		if err != nil {
			t.Fatal(err)
		}
		for key, value := range item.header {
			request.Header.Set(key, value)
		}
		response, err := http.DefaultClient.Do(request)
		if err != nil {
			t.Fatal(err)
		}
		body, _ := io.ReadAll(response.Body)
		response.Body.Close()
		if response.StatusCode != item.status {
			t.Fatalf("%s %s: status %d, want %d (%s)", item.method, item.path, response.StatusCode, item.status, body)
		}
		if !strings.Contains(string(body), item.needle) {
			t.Fatalf("%s %s: body %s lacks %s", item.method, item.path, body, item.needle)
		}
	}
}

func TestTheRingDropsTheOldestSpan(t *testing.T) {
	server, _ := startService(t, 2)
	for i := 0; i < 4; i++ {
		_, _ = get(t, server.URL+"/stats?text=x", nil)
	}
	_, body := get(t, server.URL+"/spans", nil)
	var list spanList
	if err := json.Unmarshal([]byte(body), &list); err != nil {
		t.Fatal(err)
	}
	if len(list.Spans) != 2 {
		t.Fatalf("the ring kept %d spans", len(list.Spans))
	}
	if list.Dropped == 0 {
		t.Fatal("the export must admit what it dropped")
	}
}
