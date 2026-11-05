package main

import (
	"flag"
	"fmt"
	"os"
)

func main() {
	selftest := flag.Bool("selftest", false, "run the built-in checks and exit")
	addr := flag.String("addr", "", "listen address (defaults to HOST:PORT)")
	flag.Parse()

	if *selftest {
		if failures := RunSelftest(); failures > 0 {
			fmt.Printf("selftest: %d check(s) failed\n", failures)
			os.Exit(1)
		}
		fmt.Println("selftest: all checks passed")
		return
	}
	listen := *addr
	if listen == "" {
		listen = defaultAddr()
	}
	tracker := NewTracker(NewRecorder(256))
	fmt.Printf("listening on %s\n", listen)
	if err := listenAndServe(tracker, listen); err != nil {
		fmt.Fprintf(os.Stderr, "server: %v\n", err)
		os.Exit(1)
	}
}
