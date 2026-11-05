package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
)

type checker struct {
	failures int
	checks   int
}

func (c *checker) ok(name string, condition bool) {
	c.checks++
	if !condition {
		c.failures++
		println("FAIL", name)
	}
}

func (c *checker) eq(name string, got, want string) {
	c.ok(name+" (got "+got+", want "+want+")", got == want)
}

func (c *checker) int(name string, got, want int) {
	c.ok(name, got == want)
	if got != want {
		println("FAIL", name, "got", got, "want", want)
	}
}

func runServer(request *http.Request, tracker *Tracker) *httptest.ResponseRecorder {
	recorder := httptest.NewRecorder()
	newHandler(tracker).ServeHTTP(recorder, request)
	return recorder
}

func decodeSpans(body string) spanList {
	var list spanList
	_ = json.Unmarshal([]byte(body), &list)
	return list
}

// RunSelftest returns the number of failed checks.
func RunSelftest() int {
	c := &checker{}
	const valid = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"

	parsed, err := ParseTraceparent(valid)
	c.ok("a valid header parses", err == nil)
	c.eq("the trace id survives", parsed.TraceID, "4bf92f3577b34da6a3ce929d0e0e4736")
	c.eq("the span id survives", parsed.SpanID, "00f067aa0ba902b7")
	c.ok("the sampled flag is read", parsed.Sampled())
	c.eq("it round-trips", parsed.String(), valid)

	unsampled, _ := ParseTraceparent("00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-00")
	c.ok("flags 00 means not sampled", !unsampled.Sampled())

	for name, header := range map[string]string{
		"empty":          "",
		"two fields":     "00-4bf92f3577b34da6a3ce929d0e0e4736",
		"five fields":    valid + "-extra",
		"uppercase hex":  "00-4BF92F3577B34DA6A3CE929D0E0E4736-00f067aa0ba902b7-01",
		"short trace":    "00-4bf92f35-00f067aa0ba902b7-01",
		"zero trace":     "00-00000000000000000000000000000000-00f067aa0ba902b7-01",
		"zero span":      "00-4bf92f3577b34da6a3ce929d0e0e4736-0000000000000000-01",
		"bad version":    "ff-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
		"non-hex flag":   "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-zz",
		"leading spaces": "  " + valid,
	} {
		if name == "leading spaces" {
			_, err := ParseTraceparent(header)
			c.ok("surrounding spaces are trimmed", err == nil)
			continue
		}
		_, err := ParseTraceparent(header)
		c.ok("rejects "+name, err != nil && strings.Contains(err.Error(), "invalid traceparent"))
	}

	child := parsed.Child()
	c.ok("a child keeps the trace id", child.TraceID == parsed.TraceID)
	c.ok("a child mints a new span id", child.SpanID != parsed.SpanID)
	c.ok("a child keeps the flags", child.Flags == parsed.Flags)
	c.ok("a child id is 16 lowercase hex", isLowerHex(child.SpanID, spanIDBytes))
	c.ok("minted ids differ", NewRoot().TraceID != NewRoot().TraceID)

	counts := CountText("héllo wörld\n")
	c.int("utf8 lines", counts.Lines, 1)
	c.int("utf8 words", counts.Words, 2)
	c.int("utf8 bytes", counts.Bytes, 14)
	blank := CountText("")
	c.int("empty lines", blank.Lines, 0)
	c.int("empty words", blank.Words, 0)
	c.int("empty bytes", blank.Bytes, 0)
	mixed := CountText("a b\nc\n\n")
	c.int("three lines", mixed.Lines, 3)
	c.int("three words", mixed.Words, 3)

	c.eq("percent escapes decode", percentDecode("h%C3%A9llo+w%C3%B6rld"), "héllo wörld")
	c.eq("a broken escape stays literal", percentDecode("%zz"), "%zz")
	c.eq("the first text wins", queryText("?text=one&text=two"), "one")
	c.eq("no text is empty", queryText("?other=1"), "")

	recorder := NewRecorder(2)
	recorder.Add(Span{TraceID: "a", SpanID: "1", Name: "one"})
	recorder.Add(Span{TraceID: "a", SpanID: "2", Name: "two"})
	recorder.Add(Span{TraceID: "a", SpanID: "3", Name: "three"})
	spans, dropped := recorder.Snapshot()
	c.int("the ring keeps its limit", len(spans), 2)
	c.int("it counts what it dropped", dropped, 1)
	c.eq("newest first", spans[0].SpanID, "3")
	c.eq("then the older one", spans[1].SpanID, "2")
	c.int("count agrees with the snapshot", recorder.Count(), 2)

	sampledTracker := NewTracker(NewRecorder(8))
	root := NewRoot()
	parent, finish := sampledTracker.Begin(root, "stats", map[string]string{"k": "v"})
	finish()
	stored, _ := sampledTracker.recorder.Snapshot()
	c.int("a sampled span is stored", len(stored), 1)
	c.eq("its parent is the incoming span", stored[0].ParentID, root.SpanID)
	c.eq("its trace is the incoming trace", stored[0].TraceID, root.TraceID)
	c.eq("its name is kept", stored[0].Name, "stats")
	c.ok("the finish records a duration", stored[0].EndMS >= stored[0].StartMS)
	c.eq("the caller keeps its own span id", parent.SpanID, stored[0].SpanID)

	quiet := NewTracker(NewRecorder(8))
	quietParent, quietFinish := quiet.Begin(TraceContext{TraceID: root.TraceID, SpanID: "00f067aa0ba902b7", Flags: 0}, "stats", nil)
	quietFinish()
	quietSpans, _ := quiet.recorder.Snapshot()
	c.int("an unsampled span is not stored", len(quietSpans), 0)
	c.ok("but an id is still minted", quietParent.SpanID != "")

	tracker := NewTracker(NewRecorder(16))
	request := httptest.NewRequest("GET", "/health", nil)
	response := runServer(request, tracker)
	c.int("health answers 200", response.Code, http.StatusOK)
	c.ok("health has a traceparent", strings.HasPrefix(response.Header().Get("traceparent"), "00-"))
	c.ok("health reports the count", strings.Contains(response.Body.String(), `"spans":0`))

	request = httptest.NewRequest("GET", "/stats?text=h%C3%A9llo+w%C3%B6rld%0A", nil)
	response = runServer(request, tracker)
	c.int("stats answers 200", response.Code, http.StatusOK)
	c.eq("stats wire order", response.Body.String(),
		`{"text":"héllo wörld\n","lines":1,"words":2,"bytes":14}`)
	responseTrace, _ := ParseTraceparent(response.Header().Get("traceparent"))
	c.eq("the response span id is exposed", response.Header().Get("x-span-id"), responseTrace.SpanID)

	request = httptest.NewRequest("POST", "/stats", strings.NewReader(`{"text":"a b\nc\n"}`))
	response = runServer(request, tracker)
	c.int("post answers 200", response.Code, http.StatusOK)
	c.ok("post counts 2/3/6", strings.Contains(response.Body.String(), `"lines":2,"words":3,"bytes":6`))

	request = httptest.NewRequest("POST", "/stats", strings.NewReader(`{}`))
	response = runServer(request, tracker)
	c.int("missing text is 422", response.Code, http.StatusUnprocessableEntity)
	c.ok("missing text is named", strings.Contains(response.Body.String(), `"error":"missing_text"`))

	request = httptest.NewRequest("POST", "/stats", strings.NewReader(`{"text":42}`))
	response = runServer(request, tracker)
	c.int("a non-string text is 422", response.Code, http.StatusUnprocessableEntity)

	request = httptest.NewRequest("POST", "/stats", strings.NewReader(`not json`))
	response = runServer(request, tracker)
	c.int("broken json is 422", response.Code, http.StatusUnprocessableEntity)
	c.ok("broken json names the byte", strings.Contains(response.Body.String(), "not JSON at byte"))
	c.ok("broken json carries no detail field name twice", !strings.Contains(response.Body.String(), "missing_text"))

	request = httptest.NewRequest("POST", "/stats", strings.NewReader(strings.Repeat("x", maxBody+10)))
	response = runServer(request, tracker)
	c.int("a huge body is 413", response.Code, http.StatusRequestEntityTooLarge)

	request = httptest.NewRequest("GET", "/stats", nil)
	request.Header.Set("traceparent", "00-xyz")
	response = runServer(request, tracker)
	c.int("a malformed traceparent is 400", response.Code, http.StatusBadRequest)
	c.ok("it is named", strings.Contains(response.Body.String(), `"invalid_traceparent"`))

	request = httptest.NewRequest("GET", "/stats?text=one", nil)
	request.Header.Set("traceparent", valid)
	response = runServer(request, tracker)
	c.eq("a supplied trace is echoed", response.Header().Get("x-trace-id"), "4bf92f3577b34da6a3ce929d0e0e4736")
	responseTrace, _ = ParseTraceparent(response.Header().Get("traceparent"))
	c.ok("the response span is a child", responseTrace.SpanID != "00f067aa0ba902b7")

	request = httptest.NewRequest("GET", "/stats?text=two", nil)
	request.Header.Set("traceparent", "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-00")
	response = runServer(request, tracker)
	c.int("an unsampled trace keeps flags 00", int(ParseTraceparentOrDie(response.Header().Get("traceparent")).Flags), 0)
	c.ok("and exposes no span id", response.Header().Get("x-span-id") == "")

	request = httptest.NewRequest("GET", "/spans", nil)
	response = runServer(request, tracker)
	list := decodeSpans(response.Body.String())
	c.ok("spans are exported", len(list.Spans) >= 3)
	c.ok("every span has a duration", list.Spans[0].DurationMS >= 0)
	names := map[string]bool{}
	parents := map[string]string{}
	for _, span := range list.Spans {
		names[span.Name] = true
		if span.ParentID != "" {
			parents[span.ParentID] = span.SpanID
		}
	}
	c.ok("the child span is exported", names["count"])
	c.ok("the child points at a parent", len(parents) > 0)

	request = httptest.NewRequest("GET", "/spans?trace=4bf92f3577b34da6a3ce929d0e0e4736", nil)
	response = runServer(request, tracker)
	filtered := decodeSpans(response.Body.String())
	c.ok("the trace filter keeps work", len(filtered.Spans) >= 1)
	for _, span := range filtered.Spans {
		c.ok("every filtered span matches", span.TraceID == "4bf92f3577b34da6a3ce929d0e0e4736")
	}

	request = httptest.NewRequest("GET", "/spans?trace=xyz", nil)
	response = runServer(request, tracker)
	c.int("a bad trace filter is 400", response.Code, http.StatusBadRequest)

	request = httptest.NewRequest("GET", "/nope", nil)
	response = runServer(request, tracker)
	c.int("unknown path is 404", response.Code, http.StatusNotFound)
	c.ok("404 names the route", strings.Contains(response.Body.String(), "no route for GET /nope"))

	request = httptest.NewRequest("PUT", "/health", nil)
	response = runServer(request, tracker)
	c.int("wrong method is 405", response.Code, http.StatusMethodNotAllowed)
	c.ok("405 is named", strings.Contains(response.Body.String(), "method_not_allowed"))

	request = httptest.NewRequest("DELETE", "/spans", nil)
	response = runServer(request, tracker)
	c.int("spans is read only", response.Code, http.StatusMethodNotAllowed)

	if c.failures == 0 {
		println("checks:", c.checks, "all passed")
	}
	return c.failures
}

func ParseTraceparentOrDie(header string) TraceContext {
	parsed, err := ParseTraceparent(header)
	if err != nil {
		panic(err)
	}
	return parsed
}
