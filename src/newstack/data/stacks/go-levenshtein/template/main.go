package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strings"
)

func main() {
	a := flag.String("a", "", "first string")
	b := flag.String("b", "", "second string")
	list := flag.String("list", "", "comma separated candidates for closest match")
	maxDist := flag.Int("max", 3, "maximum distance reported by closest")
	flag.Parse()

	if *a == "" {
		fmt.Fprintln(os.Stderr, "usage: app -a word [-b other] [-list a,b,c]")
		os.Exit(2)
	}

	out := map[string]any{}
	if *list != "" {
		var candidates []string
		for _, part := range strings.Split(*list, ",") {
			if c := strings.TrimSpace(part); c != "" {
				candidates = append(candidates, c)
			}
		}
		best, dist, ok := Closest(*a, candidates)
		out["closest"], out["distance"], out["withinMax"] = best, dist, ok && dist <= *maxDist
	} else {
		out["distance"] = Distance(*a, *b)
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	if err := enc.Encode(out); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
