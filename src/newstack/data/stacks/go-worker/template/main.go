package main

import (
	"flag"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"
)

func main() {
	statePath := flag.String("state", "seen.json", "path to the idempotency ledger")
	inputPath := flag.String("input", "", "NDJSON file of jobs (default: stdin)")
	maxAttempts := flag.Int("max-attempts", 3, "how many tries a retryable job gets")
	backoff := flag.Duration("backoff", 5*time.Millisecond, "base delay between retries")
	selftest := flag.Bool("selftest", false, "run the built-in checks and exit")
	flag.Parse()

	if *selftest {
		os.Exit(runSelftest())
	}
	if *maxAttempts < 1 {
		fmt.Fprintln(os.Stderr, "--max-attempts must be at least 1")
		os.Exit(2)
	}

	state, err := loadState(*statePath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "cannot read %s: %v\n", *statePath, err)
		os.Exit(2)
	}

	input := os.Stdin
	if *inputPath != "" {
		file, err := os.Open(*inputPath)
		if err != nil {
			fmt.Fprintf(os.Stderr, "cannot open %s: %v\n", *inputPath, err)
			os.Exit(2)
		}
		defer file.Close()
		input = file
	}

	stop := make(chan struct{})
	signals := make(chan os.Signal, 1)
	signal.Notify(signals, syscall.SIGTERM, syscall.SIGINT)
	go func() {
		received := <-signals
		fmt.Fprintf(os.Stderr, "%s received: draining\n", received)
		// Consume returns as soon as stop closes; the goroutine parked in
		// read(2) is abandoned rather than awaited, so the drain does not wait
		// for the producer to send another job.
		close(stop)
	}()

	worker := NewWorker(state, os.Stdout)
	worker.MaxAttempts = *maxAttempts
	worker.Backoff = *backoff
	handled := worker.Consume(input, stop)
	fmt.Fprintf(os.Stderr, "handled %d job(s)\n", handled)
}
