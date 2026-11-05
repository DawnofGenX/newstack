package main

import (
	"bytes"
	"encoding/json"
	"path/filepath"
	"testing"
	"time"
)

func newTestWorker(t *testing.T) (*Worker, *bytes.Buffer, string) {
	t.Helper()
	dir := t.TempDir()
	path := filepath.Join(dir, "seen.json")
	state, err := loadState(path)
	if err != nil {
		t.Fatalf("loadState: %v", err)
	}
	out := &bytes.Buffer{}
	worker := NewWorker(state, out)
	worker.Backoff = time.Millisecond
	worker.Sleep = func(time.Duration) {}
	return worker, out, path
}

func decode(t *testing.T, out *bytes.Buffer) map[string]any {
	t.Helper()
	var parsed map[string]any
	if err := json.Unmarshal(bytes.TrimSpace(out.Bytes()), &parsed); err != nil {
		t.Fatalf("result is not JSON: %v (%q)", err, out.String())
	}
	return parsed
}

func TestCountJob(t *testing.T) {
	worker, out, _ := newTestWorker(t)
	worker.Run([]byte(`{"id":"a","op":"count","text":"a b\nc\n"}`))
	result := decode(t, out)
	if result["status"] != "ok" || result["lines"] != float64(2) || result["words"] != float64(3) || result["bytes"] != float64(6) {
		t.Fatalf("unexpected result: %v", result)
	}
}

func TestRetryBudget(t *testing.T) {
	worker, out, _ := newTestWorker(t)
	worker.Run([]byte(`{"id":"b","op":"flaky","fail_times":5,"text":"x"}`))
	result := decode(t, out)
	if result["status"] != "failed" || result["attempts"] != float64(3) || result["code"] != "transient" {
		t.Fatalf("unexpected result: %v", result)
	}
}

func TestReplaySkipsFinishedJobs(t *testing.T) {
	worker, out, path := newTestWorker(t)
	worker.Run([]byte(`{"id":"c","op":"count","text":"x y"}`))
	out.Reset()

	state, err := loadState(path)
	if err != nil {
		t.Fatalf("loadState: %v", err)
	}
	replay := NewWorker(state, out)
	if !state.finished("c") {
		t.Fatal("the first run did not record the job")
	}
	replay.Run([]byte(`{"id":"c","op":"count","text":"different"}`))
	if status := decode(t, out)["status"]; status != "skipped" {
		t.Fatalf("want skipped, got %v", status)
	}
}

func TestDrainReadsNothingWhenStopped(t *testing.T) {
	worker, out, _ := newTestWorker(t)
	stop := make(chan struct{})
	close(stop)
	if handled := worker.Consume(bytes.NewReader([]byte(`{"id":"d","op":"count","text":"x"}`)), stop); handled != 0 {
		t.Fatalf("want 0 jobs, got %d", handled)
	}
	if out.Len() != 0 {
		t.Fatalf("want no output, got %q", out.String())
	}
}

func TestStateSurvivesAReload(t *testing.T) {
	worker, _, path := newTestWorker(t)
	worker.Run([]byte(`{"id":"e","op":"count","text":"x"}`))
	state, err := loadState(path)
	if err != nil {
		t.Fatalf("loadState: %v", err)
	}
	if state.Done["e"] != statusOK {
		t.Fatalf("want ok recorded, got %q", state.Done["e"])
	}
}
