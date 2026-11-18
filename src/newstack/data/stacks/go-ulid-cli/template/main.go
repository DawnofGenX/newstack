package main

import (
	"flag"
	"fmt"
	"os"
	"time"
)

func main() {
	gen := flag.Bool("gen", false, "generate ulids")
	parse := flag.String("parse", "", "decode a ulid")
	count := flag.Int("n", 1, "how many ulids to generate")
	at := flag.String("at", "", "RFC3339 timestamp for generated ulids")
	flag.Parse()

	if *parse != "" {
		ts, err := Timestamp(*parse)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		fmt.Println(ts.Format(time.RFC3339Nano))
		return
	}

	if !*gen {
		fmt.Fprintln(os.Stderr, "usage: app -gen [-n 3] [-at RFC3339] | app -parse ULID")
		os.Exit(2)
	}

	when := time.Now().UTC()
	if *at != "" {
		parsed, err := time.Parse(time.RFC3339, *at)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		when = parsed.UTC()
	}
	for i := 0; i < *count; i++ {
		id, err := New(when)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		fmt.Println(id)
	}
}
