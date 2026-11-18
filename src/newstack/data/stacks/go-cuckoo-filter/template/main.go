package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strings"
)

func main() {
	add := flag.String("add", "", "comma separated items to insert")
	has := flag.String("has", "", "comma separated items to look up")
	del := flag.String("del", "", "comma separated items to delete")
	capacity := flag.Int("capacity", 1000, "expected number of items")
	flag.Parse()

	filter := New(*capacity)

	for _, item := range splitList(*add) {
		if err := filter.Insert(item); err != nil {
			fmt.Fprintf(os.Stderr, "insert %q: %v\n", item, err)
			os.Exit(1)
		}
	}
	for _, item := range splitList(*del) {
		filter.Delete(item)
	}

	lookups := map[string]bool{}
	for _, item := range splitList(*has) {
		lookups[item] = filter.Lookup(item)
	}

	out := map[string]any{"size": filter.Len(), "lookups": lookups}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	if err := enc.Encode(out); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func splitList(raw string) []string {
	var out []string
	for _, part := range strings.Split(raw, ",") {
		if item := strings.TrimSpace(part); item != "" {
			out = append(out, item)
		}
	}
	return out
}
