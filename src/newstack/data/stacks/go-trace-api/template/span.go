package main

import (
	"sync"
	"time"
)

// Span is one finished unit of work, shaped for JSON export.
type Span struct {
	TraceID    string            `json:"trace_id"`
	SpanID     string            `json:"span_id"`
	ParentID   string            `json:"parent_span_id,omitempty"`
	Name       string            `json:"name"`
	StartMS    int64             `json:"start_ms"`
	EndMS      int64             `json:"end_ms"`
	DurationMS int64             `json:"duration_ms"`
	Attributes map[string]string `json:"attributes,omitempty"`
	Status     string            `json:"status"`
}

// Recorder keeps the most recent finished spans. It is a ring: when the limit is
// reached the OLDEST span goes, and the loss is counted rather than hidden.
type Recorder struct {
	mu      sync.Mutex
	spans   []Span
	limit   int
	dropped int
}

func NewRecorder(limit int) *Recorder {
	if limit < 1 {
		limit = 1
	}
	return &Recorder{limit: limit}
}

func (r *Recorder) Add(span Span) {
	r.mu.Lock()
	defer r.mu.Unlock()
	if len(r.spans) >= r.limit {
		r.spans = append(r.spans[:0], r.spans[1:]...)
		r.dropped++
	}
	r.spans = append(r.spans, span)
}

// Snapshot returns the spans NEWEST FIRST plus how many were evicted.
func (r *Recorder) Snapshot() ([]Span, int) {
	r.mu.Lock()
	defer r.mu.Unlock()
	out := make([]Span, 0, len(r.spans))
	for i := len(r.spans) - 1; i >= 0; i-- {
		out = append(out, r.spans[i])
	}
	return out, r.dropped
}

func (r *Recorder) Count() int {
	r.mu.Lock()
	defer r.mu.Unlock()
	return len(r.spans)
}

// Tracker turns a request context into spans and records the sampled ones.
type Tracker struct {
	recorder *Recorder
	now      func() time.Time
}

func NewTracker(recorder *Recorder) *Tracker {
	return &Tracker{recorder: recorder, now: time.Now}
}

// Begin returns the span the request will be attributed to and a function that finishes
// it. Unsampled traces still get ids so the header propagates, but nothing is stored.
func (t *Tracker) Begin(parent TraceContext, name string, attributes map[string]string) (*Span, func()) {
	child := parent.Child()
	started := t.now()
	span := &Span{
		TraceID:    child.TraceID,
		SpanID:     child.SpanID,
		ParentID:   parent.SpanID,
		Name:       name,
		StartMS:    started.UnixMilli(),
		Attributes: attributes,
		Status:     "ok",
	}
	finish := func() {
		ended := t.now()
		span.EndMS = ended.UnixMilli()
		span.DurationMS = ended.Sub(started).Milliseconds()
		if child.Sampled() {
			t.recorder.Add(*span)
		}
	}
	return span, finish
}
