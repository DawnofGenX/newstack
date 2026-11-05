package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"time"
)

func main() {
	addr := flag.String("addr", "", "listen address (default HOST:PORT, 127.0.0.1:8080)")
	dbPath := flag.String("db", "", "JSON file to keep accounts in (empty: memory only)")
	secret := flag.String("secret", "", "HMAC key for tokens (default TOKEN_SECRET)")
	ttl := flag.Duration("ttl", 15*time.Minute, "how long an issued token lives")
	selftest := flag.Bool("selftest", false, "run the in-process checks and exit")
	flag.Parse()

	if *selftest {
		os.Exit(runSelftest())
	}

	if *addr == "" {
		port, err := parsePort(envOr("PORT", "8080"))
		if err != nil {
			fmt.Fprintf(os.Stderr, "blog-count: bad PORT %q: %v\n", os.Getenv("PORT"), err)
			os.Exit(2)
		}
		*addr = fmt.Sprintf("%s:%d", envOr("HOST", "127.0.0.1"), port)
	}

	key := *secret
	if key == "" {
		key = envOr("TOKEN_SECRET", "")
	}
	if key == "" {
		fmt.Fprintln(os.Stderr, "blog-count: set TOKEN_SECRET or pass --secret")
		os.Exit(2)
	}

	store, err := NewStore(*dbPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "blog-count: cannot read %s: %v\n", *dbPath, err)
		os.Exit(2)
	}
	h := &handler{
		store:  store,
		tokens: newTokenizer([]byte(key), *ttl, time.Now),
		now:    time.Now,
	}
	log.Printf("listening on %s (%d accounts, ttl %s)", *addr, store.Count(), *ttl)
	if err := listenAndServe(*addr, h); err != nil {
		log.Printf("stopped: %v", err)
		os.Exit(1)
	}
}
