package app

import (
	"bufio"
	"flag"
	"fmt"
	"io"
	"strings"

	"{{ npm_name }}/internal/cache"
)

const Version = "0.1.0"

func Run(args []string, stdin io.Reader, stdout, stderr io.Writer) int {
	fs := flag.NewFlagSet("lru", flag.ContinueOnError)
	fs.SetOutput(stderr)
	capacity := fs.Int("capacity", 3, "max entries")
	ttl := fs.Duration("ttl", 0, "TTL duration (0 = none)")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return 0
		}
		return 2
	}

	c := cache.New[string, string](*capacity, *ttl)

	scanner := bufio.NewScanner(stdin)
	scanner.Buffer(make([]byte, 1024*1024), 1024*1024)
	processed := 0
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}
		fields := strings.Fields(line)
		switch strings.ToUpper(fields[0]) {
		case "PUT":
			if len(fields) < 3 {
				fmt.Fprintln(stderr, "usage: PUT key value")
				return 2
			}
			c.Put(fields[1], strings.Join(fields[2:], " "))
			fmt.Fprintf(stdout, "PUT %s\n", fields[1])
		case "GET":
			if len(fields) < 2 {
				fmt.Fprintln(stderr, "usage: GET key")
				return 2
			}
			if v, ok := c.Get(fields[1]); ok {
				fmt.Fprintf(stdout, "HIT %s %s\n", fields[1], v)
			} else {
				fmt.Fprintf(stdout, "MISS %s\n", fields[1])
			}
		default:
			fmt.Fprintf(stderr, "unknown op %q\n", fields[0])
			return 2
		}
		processed++
	}
	hits, misses := c.Stats()
	fmt.Fprintf(stdout, "stats: hits=%d misses=%d size=%d\n", hits, misses, c.Len())
	return 0
}
