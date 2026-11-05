package main

import (
	"bufio"
	"encoding/json"
	"errors"
	"io"
	"time"
)

// Worker turns jobs into results. It owns no goroutines: the caller decides how
// to read input, which is what lets a signal interrupt a run between jobs.
type Worker struct {
	State       *State
	MaxAttempts int
	Backoff     time.Duration
	Sleep       func(time.Duration)
	Out         io.Writer
}

func NewWorker(state *State, out io.Writer) *Worker {
	return &Worker{
		State:       state,
		MaxAttempts: 3,
		Backoff:     5 * time.Millisecond,
		Sleep:       time.Sleep,
		Out:         out,
	}
}

// Run handles one job line and returns the result that was written.
func (w *Worker) Run(line []byte) Result {
	job, err := decodeJob(line)
	if err != nil {
		var failure *jobError
		if errors.As(err, &failure) {
			result := Result{Status: statusFailed, Code: failure.code, Detail: failure.detail}
			w.emit(result)
			return result
		}
		result := Result{Status: statusFailed, Code: "invalid_json", Detail: err.Error()}
		w.emit(result)
		return result
	}

	if w.State != nil && w.State.finished(job.ID) {
		result := Result{ID: job.ID, Status: statusSkipped}
		w.emit(result)
		return result
	}

	result := Result{ID: job.ID}
	for tries := 1; tries <= w.MaxAttempts; tries++ {
		result.Attempts = tries
		counts, err := attempt(job, tries)
		if err == nil {
			result.Status = statusOK
			result.Counts = counts
			break
		}
		var failure *jobError
		if !errors.As(err, &failure) {
			result.Status = statusFailed
			result.Code = "internal"
			result.Detail = err.Error()
			break
		}
		if !failure.retryable {
			result.Status = statusFailed
			result.Code = failure.code
			result.Detail = failure.detail
			break
		}
		if tries == w.MaxAttempts {
			result.Status = statusFailed
			result.Code = failure.code
			result.Detail = failure.detail
			break
		}
		// Back off before the next try; the first retry waits one interval.
		w.Sleep(time.Duration(tries) * w.Backoff)
	}

	if w.State != nil && result.ID != "" {
		w.State.record(result.ID, result.Status)
		if err := w.State.save(); err != nil {
			result.Status = statusFailed
			result.Code = "state_write"
			result.Detail = err.Error()
		}
	}
	w.emit(result)
	return result
}

func (w *Worker) emit(result Result) {
	raw, err := json.Marshal(result)
	if err != nil {
		return
	}
	w.Out.Write(append(raw, '\n'))
}

// Consume reads NDJSON jobs until the reader ends or stop is closed. It returns
// the number of jobs it handled; a stop leaves the current job finished and the
// rest of the input unread, which is what a drain means.
//
// The scan runs in its own goroutine because read(2) on a pipe cannot be
// cancelled: a signal that only closed the stop channel would be stuck behind a
// blocked read until the producer wrote another job.
func (w *Worker) Consume(input io.Reader, stop <-chan struct{}) int {
	lines := make(chan []byte)
	go func() {
		defer close(lines)
		scanner := bufio.NewScanner(input)
		scanner.Buffer(make([]byte, 0, 64*1024), 4*1024*1024)
		for scanner.Scan() {
			line := append([]byte(nil), scanner.Bytes()...)
			select {
			case lines <- line:
			case <-stop:
				return
			}
		}
	}()

	handled := 0
	for {
		select {
		case <-stop:
			return handled
		case line, ok := <-lines:
			if !ok {
				return handled
			}
			if len(line) == 0 {
				continue
			}
			w.Run(line)
			handled++
		}
	}
}
