package main

import (
	"flag"
	"fmt"
	"os"
	"time"
)

const usageText = `usage: %s -spec "*/15 * * * *" [-from RFC3339] [-count N]

Prints the next times a five-field cron expression fires. The fields are
minute, hour, day of month, month and day of week (0 or 7 is Sunday), and each
accepts *, */n, a-b, a-b/n and comma lists. Times are UTC unless -from carries
a zone.
`

func run(args []string, stdout, stderr *os.File) int {
	flags := flag.NewFlagSet("{{ npm_name }}", flag.ContinueOnError)
	flags.SetOutput(stderr)
	spec := flags.String("spec", "", "cron expression")
	from := flags.String("from", "", "start time, RFC3339 (default: now)")
	count := flags.Int("count", 5, "how many occurrences to print")
	if err := flags.Parse(args); err != nil {
		return 2
	}
	if *spec == "" {
		fmt.Fprintf(stderr, usageText, "{{ npm_name }}")
		return 2
	}
	schedule, err := Parse(*spec)
	if err != nil {
		fmt.Fprintf(stderr, "invalid spec: %v\n", err)
		return 1
	}
	start := time.Now().UTC()
	if *from != "" {
		start, err = time.Parse(time.RFC3339, *from)
		if err != nil {
			fmt.Fprintf(stderr, "invalid -from: %v\n", err)
			return 1
		}
	}
	times, err := schedule.Upcoming(start, *count)
	if err != nil {
		fmt.Fprintf(stderr, "%v\n", err)
		return 1
	}
	for _, at := range times {
		fmt.Fprintln(stdout, at.UTC().Format(time.RFC3339))
	}
	return 0
}

func main() {
	os.Exit(run(os.Args[1:], os.Stdout, os.Stderr))
}
