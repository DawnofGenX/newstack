package main

import (
	"encoding/json"
	"fmt"
)

// Job is one line of input. Only "count" and "flaky" exist on purpose: the
// worker has to fit in a reader's head, and "flaky" is what makes the retry
// policy testable without a real network.
type Job struct {
	ID        string `json:"id"`
	Op        string `json:"op"`
	Text      string `json:"text"`
	FailTimes int    `json:"fail_times"`
}

// Result is one line of output.
type Result struct {
	ID       string `json:"id"`
	Status   string `json:"status"`
	Attempts int    `json:"attempts"`
	Counts
	Code   string `json:"code,omitempty"`
	Detail string `json:"detail,omitempty"`
}

const (
	statusOK      = "ok"
	statusFailed  = "failed"
	statusSkipped = "skipped"
)

// jobError says whether trying again could help. Retrying a bad op or a broken
// line just wastes the budget, so those are permanent.
type jobError struct {
	code      string
	detail    string
	retryable bool
}

func (e *jobError) Error() string { return e.code + ": " + e.detail }

func permanent(code, detail string) *jobError {
	return &jobError{code: code, detail: detail, retryable: false}
}

func transient(detail string) *jobError {
	return &jobError{code: "transient", detail: detail, retryable: true}
}

func decodeJob(line []byte) (Job, error) {
	var job Job
	if err := json.Unmarshal(line, &job); err != nil {
		return Job{}, permanent("invalid_json", err.Error())
	}
	if job.ID == "" {
		return Job{}, permanent("missing_id", "every job carries an id")
	}
	return job, nil
}

// attempt runs one try of a job.
func attempt(job Job, tries int) (Counts, error) {
	switch job.Op {
	case "count":
		return countText(job.Text), nil
	case "flaky":
		if tries <= job.FailTimes {
			return Counts{}, transient(fmt.Sprintf("asked to fail on try %d", tries))
		}
		return countText(job.Text), nil
	default:
		return Counts{}, permanent("unknown_op", fmt.Sprintf("no handler for %q", job.Op))
	}
}
