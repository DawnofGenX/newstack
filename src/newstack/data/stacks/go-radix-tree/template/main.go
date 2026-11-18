package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strings"
)

func main() {
	entries := flag.String("set", "", "comma separated key=value pairs to insert")
	get := flag.String("get", "", "key to look up")
	match := flag.String("match", "", "string whose longest stored prefix is reported")
	keys := flag.Bool("keys", false, "print every stored key")
	flag.Parse()

	tree := New()
	for _, pair := range strings.Split(*entries, ",") {
		pair = strings.TrimSpace(pair)
		if pair == "" {
			continue
		}
		parts := strings.SplitN(pair, "=", 2)
		if len(parts) != 2 {
			fmt.Fprintf(os.Stderr, "invalid pair %q, want key=value\n", pair)
			os.Exit(1)
		}
		tree.Insert(strings.TrimSpace(parts[0]), strings.TrimSpace(parts[1]))
	}

	out := map[string]any{"keys": tree.Keys(), "size": tree.Len()}
	if *get != "" {
		value, ok := tree.Get(*get)
		out["get"] = map[string]any{"key": *get, "value": value, "found": ok}
	}
	if *match != "" {
		key, value, ok := tree.LongestPrefix(*match)
		out["longestPrefix"] = map[string]any{"key": key, "value": value, "found": ok}
	}
	if !*keys {
		delete(out, "keys")
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	if err := enc.Encode(out); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
