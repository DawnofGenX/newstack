package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"strconv"
	"strings"
)

const maxBody = 64 << 10

// statsResponse pins the wire order: text first, then the three counts.
type statsResponse struct {
	Text  string `json:"text"`
	Lines int    `json:"lines"`
	Words int    `json:"words"`
	Bytes int    `json:"bytes"`
}

type errorBody struct {
	Error  string `json:"error"`
	Detail string `json:"detail,omitempty"`
}

type spanList struct {
	Spans   []Span `json:"spans"`
	Dropped int    `json:"dropped"`
}

type handler struct {
	tracker *Tracker
}

func newHandler(tracker *Tracker) *handler { return &handler{tracker: tracker} }

func (h *handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	switch {
	case r.URL.Path == "/health":
		h.only(w, r, "GET", h.health)
	case r.URL.Path == "/stats":
		h.anyOf(w, r, []string{"GET", "POST"}, h.stats)
	case r.URL.Path == "/spans":
		h.only(w, r, "GET", h.spans)
	default:
		writeJSON(w, http.StatusNotFound, errorBody{
			Error:  "not_found",
			Detail: fmt.Sprintf("no route for %s %s", r.Method, r.URL.Path),
		})
	}
}

func (h *handler) only(w http.ResponseWriter, r *http.Request, method string, next func(http.ResponseWriter, *http.Request, TraceContext)) {
	if r.Method != method {
		writeJSON(w, http.StatusMethodNotAllowed, errorBody{Error: "method_not_allowed"})
		return
	}
	h.withTrace(w, r, next)
}

func (h *handler) anyOf(w http.ResponseWriter, r *http.Request, methods []string, next func(http.ResponseWriter, *http.Request, TraceContext)) {
	for _, method := range methods {
		if r.Method == method {
			h.withTrace(w, r, next)
			return
		}
	}
	writeJSON(w, http.StatusMethodNotAllowed, errorBody{Error: "method_not_allowed"})
}

// withTrace parses (or mints) the trace context, answers 400 for a malformed header,
// then hands the handler a context whose span id becomes the response header.
func (h *handler) withTrace(w http.ResponseWriter, r *http.Request, next func(http.ResponseWriter, *http.Request, TraceContext)) {
	incoming := TraceContext{}
	header := r.Header.Get("traceparent")
	if header == "" {
		incoming = NewRoot()
	} else {
		parsed, err := ParseTraceparent(header)
		if err != nil {
			writeJSON(w, http.StatusBadRequest, errorBody{Error: "invalid_traceparent", Detail: err.Error()})
			return
		}
		incoming = parsed
	}
	w.Header().Set("traceparent", incoming.String())
	w.Header().Set("x-trace-id", incoming.TraceID)
	next(w, r, incoming)
}

func (h *handler) health(w http.ResponseWriter, r *http.Request, trace TraceContext) {
	writeJSON(w, http.StatusOK, struct {
		Status string `json:"status"`
		Spans  int    `json:"spans"`
	}{Status: "ok", Spans: h.tracker.recorder.Count()})
}

func (h *handler) stats(w http.ResponseWriter, r *http.Request, trace TraceContext) {
	span, finish := h.tracker.Begin(trace, "stats", map[string]string{
		"http.method": r.Method,
		"http.route":  "/stats",
	})
	defer finish()
	// Announce the span that actually served the request; the incoming id was only
	// the parent.
	w.Header().Set("traceparent", TraceContext{TraceID: span.TraceID, SpanID: span.SpanID, Flags: trace.Flags}.String())

	var text string
	status := http.StatusOK
	if r.Method == "POST" {
		raw, err := io.ReadAll(io.LimitReader(r.Body, maxBody+1))
		if err != nil {
			span.Status = "error"
			writeJSON(w, http.StatusBadRequest, errorBody{Error: "invalid_body"})
			return
		}
		if len(raw) > maxBody {
			span.Status = "error"
			span.Attributes["error"] = "body_too_large"
			writeJSON(w, http.StatusRequestEntityTooLarge, errorBody{Error: "body_too_large"})
			return
		}
		parsed, kind, detail := readTextMember(raw)
		if kind != "text" {
			span.Status = "error"
			span.Attributes["error"] = kind
			status = http.StatusUnprocessableEntity
			writeJSON(w, status, errorBody{Error: kind, Detail: detail})
			return
		}
		text = parsed
	} else {
		text = queryText(r.URL.RawQuery)
	}

	// A child span shows the parent link the export must reproduce.
	child, finishChild := h.tracker.Begin(TraceContext{TraceID: span.TraceID, SpanID: span.SpanID, Flags: trace.Flags}, "count", map[string]string{
		"text.bytes": strconv.Itoa(len(text)),
	})
	counts := CountText(text)
	finishChild()

	if child.SpanID == span.SpanID {
		panic("a child span must never reuse the parent id")
	}
	span.Attributes["text.bytes"] = strconv.Itoa(counts.Bytes)
	span.Attributes["text.lines"] = strconv.Itoa(counts.Lines)
	span.Attributes["text.words"] = strconv.Itoa(counts.Words)
	span.Attributes["sample.sampled"] = strconv.FormatBool(trace.Sampled())

	if trace.Sampled() {
		w.Header().Set("x-span-id", span.SpanID)
	}
	writeJSON(w, status, statsResponse{Text: text, Lines: counts.Lines, Words: counts.Words, Bytes: counts.Bytes})
}

func (h *handler) spans(w http.ResponseWriter, r *http.Request, trace TraceContext) {
	spans, dropped := h.tracker.recorder.Snapshot()
	if filter := r.URL.Query().Get("trace"); filter != "" {
		if !isLowerHex(filter, traceIDBytes) {
			writeJSON(w, http.StatusBadRequest, errorBody{Error: "invalid_trace", Detail: "the trace query must be 32 lowercase hex digits"})
			return
		}
		kept := make([]Span, 0, len(spans))
		for _, span := range spans {
			if span.TraceID == filter {
				kept = append(kept, span)
			}
		}
		spans = kept
	}
	writeJSON(w, http.StatusOK, spanList{Spans: spans, Dropped: dropped})
}

// queryText takes the FIRST text occurrence, like a URL query parser does.
func queryText(raw string) string {
	raw = strings.TrimPrefix(raw, "?")
	for _, pair := range strings.Split(raw, "&") {
		if pair == "" {
			continue
		}
		key, value, _ := strings.Cut(pair, "=")
		if percentDecode(key) == "text" {
			return percentDecode(value)
		}
	}
	return ""
}

func percentDecode(value string) string {
	var out []byte
	for i := 0; i < len(value); i++ {
		switch value[i] {
		case '+':
			out = append(out, ' ')
		case '%':
			if i+2 < len(value) {
				if decoded, err := strconv.ParseUint(value[i+1:i+3], 16, 8); err == nil {
					out = append(out, byte(decoded))
					i += 2
					continue
				}
			}
			out = append(out, '%')
		default:
			out = append(out, value[i])
		}
	}
	return string(out)
}

// readTextMember walks the JSON just far enough to find a top-level "text" string.
// It never re-serialises: the bytes as sent are the bytes counted.
func readTextMember(raw []byte) (string, string, string) {
	var payload map[string]json.RawMessage
	if err := json.Unmarshal(raw, &payload); err != nil {
		var syntax *json.SyntaxError
		if errors.As(err, &syntax) {
			return "", "invalid_json", fmt.Sprintf("not JSON at byte %d", syntax.Offset)
		}
		return "", "invalid_json", "the body must be a JSON object"
	}
	member, ok := payload["text"]
	if !ok {
		return "", "missing_text", "the body needs a \"text\" member"
	}
	var text string
	if err := json.Unmarshal(member, &text); err != nil {
		return "", "missing_text", "the \"text\" member must be a string"
	}
	return text, "text", ""
}

func writeJSON(w http.ResponseWriter, status int, payload any) {
	body, err := json.Marshal(payload)
	if err != nil {
		http.Error(w, `{"error":"internal_error"}`, http.StatusInternalServerError)
		return
	}
	w.Header().Set("content-type", "application/json; charset=utf-8")
	w.Header().Set("content-length", strconv.Itoa(len(body)))
	w.WriteHeader(status)
	_, _ = w.Write(body)
}
