# {{ project_name }}

{{ description }}

A batch worker, not a service: it reads NDJSON jobs from stdin (or `--input`),
writes one NDJSON result per job to stdout, and keeps an idempotency ledger so a
replayed file does not redo the work.

## What is here

| Path | What lives there |
| --- | --- |
| `counts.go` | byte-exact line/word/byte counting |
| `job.go` | the job and result shapes, and a typed error that says whether a retry could help |
| `state.go` | the ledger (`seen.json`): loaded at start, written with temp file + rename |
| `worker.go` | the retry loop and `Consume`, which reads jobs in its own goroutine |
| `main.go` | flags, signal handling, exit codes |
| `selftest.go` | 32 checks behind `--selftest`, no test framework |
| `worker_test.go` | the same behaviour under `go test` |
| `jobs.ndjson` | a fixture with a success, a flaky job, a job that never succeeds, and two broken ones |
| `run.sh` | builds the binary, runs the fixture twice, then interrupts a live stream |

## Run it

```bash
make build
./bin/{{ npm_name }} --selftest
./bin/{{ npm_name }} --input jobs.ndjson --state seen.json
```

```jsonc
{"id":"one","op":"count","text":"a b\nc\n"}   // {"id":"one","status":"ok","attempts":1,"lines":2,"words":3,"bytes":6}
{"id":"two","op":"flaky","fail_times":2,"text":"x"}
```

Run the same file again and the finished jobs come back as `"status":"skipped"`;
a job that failed keeps retrying, because a retry budget exists to be used on a
replay. `"attempts"` is in every result, so the retry policy is visible in the
output rather than in a log line.

## Traps this starter already paid for

- **`read(2)` on a pipe cannot be cancelled.** The obvious drain — `signal` →
  close a channel, check it between jobs — leaves the process asleep in
  `scanner.Scan()` until the producer writes another job, so SIGTERM looks
  ignored and the orchestrator escalates to SIGKILL. `Consume` runs the scan in
  its own goroutine and returns as soon as `stop` closes; the parked goroutine is
  abandoned, which is fine because the process is exiting.
- **`os.File.SetReadDeadline` is not the fix.** On a FIFO inherited as stdin the
  call can succeed and still not interrupt the pending read.
- **Writing the ledger is the crash-safety point.** `os.WriteFile` truncates and
  then writes: a kill in between leaves an empty ledger, and the whole input is
  replayed. `save()` writes a temp file, `Sync`s, and `Rename`s over the target.
- **A failed job must be recorded but not treated as finished.** Recording only
  successes means a replay cannot tell "never seen" from "seen and failed", and
  recording failures as done means a replay silently drops work. The ledger keeps
  the status and only `"ok"` counts as finished.
- **Retry every error and you retry typos.** `invalid_json`, `missing_id` and
  `unknown_op` are permanent; only `transient` spends the budget. Without that
  split a bad line burns three attempts and 15 ms of backoff for nothing.
- **`go build` needs the output directory.** `-o bin/{{ npm_name }}` fails when
  `bin/` does not exist yet; the Makefile target creates it via `go build`'s own
  `bin` path only because `build` depends on nothing else — run `mkdir -p bin`
  first if you build by hand.
- **One result per line, flushed per job.** Buffering the whole output means a
  job's result is lost when the process is drained; every result is written and
  the ledger is saved before the next job is read.
