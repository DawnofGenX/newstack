package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

type checkbook struct {
	failures int
	total    int
}

func (c *checkbook) check(name string, ok bool, detail string) {
	c.total++
	if ok {
		fmt.Printf("ok %s\n", name)
		return
	}
	c.failures++
	if detail == "" {
		fmt.Printf("FAIL %s\n", name)
		return
	}
	fmt.Printf("FAIL %s: %s\n", name, detail)
}

// quietly runs one job line and returns the decoded result.
func (c *checkbook) job(worker *Worker, line string) map[string]any {
	worker.Run([]byte(line))
	var parsed map[string]any
	raw := worker.Out.(*bytes.Buffer) //nolint:errcheck // only selftest builds this
	lines := strings.Split(strings.TrimSpace(raw.String()), "\n")
	last := lines[len(lines)-1]
	raw.Reset()

	if err := json.Unmarshal([]byte(last), &parsed); err != nil {
		c.check("result is JSON", false, err.Error())
		return map[string]any{}
	}
	return parsed
}

func runSelftest() int {
	book := &checkbook{}
	dir, err := os.MkdirTemp("", "worker-selftest-")
	if err != nil {
		fmt.Println(err)
		return 2
	}
	defer os.RemoveAll(dir)

	// counting
	cases := []struct {
		text  string
		lines int
		words int
		bytes int
	}{
		{"", 0, 0, 0},
		{"hello world\n", 1, 2, 12},
		{"a b\nc\n", 2, 3, 6},
		{"héllo wörld\n", 1, 2, 14},
		{"  padded  ", 0, 1, 10},
		{"a\tb\vc\fd", 0, 4, 7},
		{"\n\n\n", 3, 0, 3},
	}
	for _, test := range cases {
		counts := countText(test.text)
		book.check(fmt.Sprintf("counts %q", test.text),
			counts.Lines == test.lines && counts.Words == test.words && counts.Bytes == test.bytes,
			fmt.Sprintf("got %+v", counts))
	}

	// decoding
	_, err = decodeJob([]byte("{"))
	book.check("broken json is permanent", err != nil && !err.(*jobError).retryable, "")
	_, err = decodeJob([]byte(`{"op":"count","text":"x"}`))
	book.check("a job without an id is rejected", err != nil && err.(*jobError).code == "missing_id", "")
	job, err := decodeJob([]byte(`{"id":"a","op":"count","text":"x y"}`))
	book.check("a good job decodes", err == nil && job.ID == "a" && job.Op == "count", "")

	// attempts and retries
	state, err := loadState(filepath.Join(dir, "seen.json"))
	book.check("a missing ledger loads empty", err == nil && len(state.Done) == 0, "")

	out := &bytes.Buffer{}
	worker := NewWorker(state, out)
	worker.Backoff = time.Millisecond
	slept := 0
	worker.Sleep = func(time.Duration) { slept++ }

	result := book.job(worker, `{"id":"one","op":"count","text":"a b\nc\n"}`)
	book.check("count ok", result["status"] == "ok", fmt.Sprint(result))
	book.check("count numbers", result["lines"] == float64(2) && result["words"] == float64(3) && result["bytes"] == float64(6), fmt.Sprint(result))
	book.check("one attempt", result["attempts"] == float64(1), fmt.Sprint(result))
	book.check("no sleeping on success", slept == 0, fmt.Sprint(slept))

	result = book.job(worker, `{"id":"two","op":"flaky","fail_times":2,"text":"x"}`)
	book.check("flaky succeeds on the third try", result["status"] == "ok" && result["attempts"] == float64(3), fmt.Sprint(result))
	book.check("backoff between retries", slept == 2, fmt.Sprint(slept))

	result = book.job(worker, `{"id":"three","op":"flaky","fail_times":9,"text":"x"}`)
	book.check("a job that never succeeds fails", result["status"] == "failed", fmt.Sprint(result))
	book.check("failure keeps the code", result["code"] == "transient", fmt.Sprint(result))
	book.check("failure stops at the budget", result["attempts"] == float64(3), fmt.Sprint(result))

	result = book.job(worker, `{"id":"four","op":"nope","text":"x"}`)
	book.check("unknown op is permanent", result["status"] == "failed" && result["code"] == "unknown_op" && result["attempts"] == float64(1), fmt.Sprint(result))

	result = book.job(worker, `{"op":"count"}`)
	book.check("a job without an id produces no id", result["code"] == "missing_id", fmt.Sprint(result))

	// idempotency
	raw, err := os.ReadFile(filepath.Join(dir, "seen.json"))
	book.check("ledger is written", err == nil && len(raw) > 0, fmt.Sprint(err))
	book.check("ledger records the success", strings.Contains(string(raw), `"one": "ok"`), string(raw))
	book.check("ledger records the failure", strings.Contains(string(raw), `"three": "failed"`), string(raw))

	replayed, err := loadState(filepath.Join(dir, "seen.json"))
	book.check("ledger reloads", err == nil, "")
	replayWorker := NewWorker(replayed, out)
	result = book.job(replayWorker, `{"id":"one","op":"count","text":"completely different"}`)
	book.check("a finished job is skipped", result["status"] == "skipped", fmt.Sprint(result))
	result = book.job(replayWorker, `{"id":"three","op":"count","text":"x"}`)
	book.check("a failed job is retried on replay", result["status"] == "ok", fmt.Sprint(result))

	// drain
	state2, _ := loadState(filepath.Join(dir, "drain.json"))
	drainOut := &bytes.Buffer{}
	drainWorker := NewWorker(state2, drainOut)
	drainWorker.Backoff = time.Millisecond
	stop := make(chan struct{})
	close(stop)
	handled := drainWorker.Consume(strings.NewReader(`{"id":"x","op":"count","text":"a"}`), stop)
	book.check("a closed stop reads nothing", handled == 0 && drainOut.Len() == 0, fmt.Sprint(handled))

	// reading
	fullOut := &bytes.Buffer{}
	state3, _ := loadState(filepath.Join(dir, "full.json"))
	fullWorker := NewWorker(state3, fullOut)
	fullWorker.Backoff = time.Millisecond
	handled = fullWorker.Consume(strings.NewReader(
		"{\"id\":\"a\",\"op\":\"count\",\"text\":\"x\"}\n\n{\"id\":\"b\",\"op\":\"count\",\"text\":\"y\"}\n",
	), make(chan struct{}))
	book.check("blank lines are skipped", handled == 2, fmt.Sprint(handled))
	book.check("one result per job", strings.Count(fullOut.String(), "\n") == 2, fullOut.String())

	// a ledger in a directory that does not exist yet
	nested := filepath.Join(dir, "deep", "deeper", "seen.json")
	state4, err := loadState(nested)
	nestedWorker := NewWorker(state4, &bytes.Buffer{})
	nestedWorker.Run([]byte(`{"id":"n","op":"count","text":"x"}`))
	book.check("the ledger directory is created", err == nil && fileExists(nested), nested)

	if book.failures == 0 {
		fmt.Printf("checks: %d, all passed\n", book.total)
		return 0
	}
	fmt.Printf("checks: %d, failed: %d\n", book.total, book.failures)
	return 1
}

func fileExists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}
