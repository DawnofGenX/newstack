package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"
)

const prog = "wal-cache"

func main() {
	os.Exit(run(os.Args[1:]))
}

func run(args []string) int {
	var (
		addr     string
		dir      string
		selftest bool
	)
	flags := flag.NewFlagSet(prog, flag.ContinueOnError)
	flags.StringVar(&dir, "dir", "wal", "directory that holds the log segments")
	flags.StringVar(&addr, "addr", "", "listen address, defaults to HOST:PORT")
	flags.BoolVar(&selftest, "selftest", false, "run the self-checks and exit")
	if err := flags.Parse(args); err != nil {
		return 2
	}

	if selftest {
		return runSelftest()
	}

	if addr == "" {
		var err error
		addr, err = defaultAddr()
		if err != nil {
			fmt.Fprintf(os.Stderr, "%s: %v\n", prog, err)
			return 2
		}
	}

	store, err := Open(dir)
	if err != nil {
		fmt.Fprintf(os.Stderr, "%s: %v\n", prog, err)
		return 1
	}
	defer store.Close()

	recovered := store.Recovery()
	server, port, err := Listen(store, addr)
	if err != nil {
		fmt.Fprintf(os.Stderr, "%s: %v\n", prog, err)
		return 1
	}
	fmt.Printf("%s: listening on %s (log %s, %d segment(s), %d record(s))\n",
		prog, addr, dir, recovered.Segments, recovered.Records)
	if recovered.TornTail {
		fmt.Printf("%s: dropped a torn tail of %d bytes\n", prog, recovered.DiscardedBytes)
	}

	signals := make(chan os.Signal, 1)
	signal.Notify(signals, syscall.SIGINT, syscall.SIGTERM)

	done := make(chan struct{})
	go func() {
		defer close(done)
		if err := server.Serve(); err != nil {
			fmt.Fprintf(os.Stderr, "%s: %v\n", prog, err)
		}
	}()

	signalNumber := 0
	select {
	case received := <-signals:
		signalNumber = int(received.(syscall.Signal))
		fmt.Printf("%s: signal %d received: draining\n", prog, signalNumber)
	case <-done:
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := server.Shutdown(ctx); err != nil {
		fmt.Fprintf(os.Stderr, "%s: %v\n", prog, err)
		return 1
	}
	_ = port
	return 0
}
