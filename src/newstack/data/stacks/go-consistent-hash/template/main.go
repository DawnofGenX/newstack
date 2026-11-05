package main

import (
	"context"
	"flag"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"
)

const defaultPort = "5490"

func main() {
	addr := flag.String("addr", "", "host:port to listen on (defaults from HOST/PORT env)")
	replicas := flag.Int("replicas", 2, "replication factor (first N ring owners)")
	selftest := flag.Bool("selftest", false, "run in-process selftest and exit")
	flag.Parse()

	if *selftest {
		os.Exit(runSelftest())
	}

	host := "0.0.0.0"
	port := defaultPort
	if h := os.Getenv("HOST"); h != "" {
		host = h
	}
	if p := os.Getenv("PORT"); p != "" {
		n, err := strconv.Atoi(p)
		if err != nil || n < 1 || n > 65535 {
			fmt.Fprintf(os.Stderr, "{{ npm_name }}: bad PORT %q: want integer 1-65535\n", p)
			os.Exit(2)
		}
		port = strconv.Itoa(n)
	}
	listenAddr := host + ":" + port
	if *addr != "" {
		listenAddr = *addr
	}

	names := []string{"alpha", "beta", "gamma"}
	cluster := NewCluster(names, *replicas, nil)
	server := &http.Server{
		Addr:              listenAddr,
		Handler:           NewHandler(cluster),
		ReadHeaderTimeout: 5 * time.Second,
	}

	go func() {
		fmt.Printf("{{ npm_name }}: listening on %s nodes=%v replicas=%d\n", listenAddr, names, *replicas)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			fmt.Fprintf(os.Stderr, "{{ npm_name }}: serve failed: %v\n", err)
			os.Exit(1)
		}
	}()

	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGTERM, syscall.SIGINT)
	s := <-sig
	num := 0
	if st, ok := s.(syscall.Signal); ok {
		num = int(st)
	}
	fmt.Printf("{{ npm_name }}: signal %d received: draining\n", num)

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := server.Shutdown(ctx); err != nil {
		fmt.Fprintf(os.Stderr, "{{ npm_name }}: drain failed: %v\n", err)
		os.Exit(1)
	}
	fmt.Println("{{ npm_name }}: drained")
}
