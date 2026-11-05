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

func main() {
	addr := flag.String("addr", defaultAddr(), "address to listen on")
	idle := flag.Duration("idle", 30*time.Second, "drop a connection after this much silence")
	selftest := flag.Bool("selftest", false, "run the in-process checks and exit")
	flag.Parse()

	if *selftest {
		if err := RunSelfTest(); err != nil {
			fmt.Fprintf(os.Stderr, "selftest: %v\n", err)
			os.Exit(1)
		}
		return
	}

	server, err := Listen(*addr, *idle)
	if err != nil {
		fmt.Fprintf(os.Stderr, "cannot listen on %s: %v\n", *addr, err)
		os.Exit(1)
	}
	fmt.Printf("listening on %s (frames up to %d bytes)\n", server.Addr(), MaxFrame)

	signals := make(chan os.Signal, 1)
	signal.Notify(signals, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-signals
		fmt.Fprintln(os.Stderr, "received a signal: draining")
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		_ = server.Shutdown(ctx)
		os.Exit(0)
	}()

	if err := server.Serve(); err != nil {
		fmt.Fprintf(os.Stderr, "serve: %v\n", err)
		os.Exit(1)
	}
}

func defaultAddr() string {
	host := os.Getenv("HOST")
	if host == "" {
		host = "127.0.0.1"
	}
	port := os.Getenv("PORT")
	if port == "" {
		port = "5481"
	}
	return host + ":" + port
}
