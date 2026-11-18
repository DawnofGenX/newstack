package main

import (
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
)

const usageText = `Usage: {{ npm_name }} [options]

Reads a sitemap.xml document from stdin or --file, validates it and prints a
short summary. Use --render to print the normalised document instead.

Options:
  -file PATH   read the sitemap from PATH instead of stdin
  -render      print the normalised sitemap XML
  -h           show this message
`

func main() {
	os.Exit(run(os.Args[1:], os.Stdin, os.Stdout, os.Stderr))
}

func run(args []string, stdin io.Reader, stdout, stderr io.Writer) int {
	flags := flag.NewFlagSet("{{ npm_name }}", flag.ContinueOnError)
	flags.SetOutput(stderr)
	path := flags.String("file", "", "read the sitemap from this file instead of stdin")
	render := flags.Bool("render", false, "print the normalised sitemap XML")
	flags.Usage = func() { fmt.Fprint(stderr, usageText) }
	if err := flags.Parse(args); err != nil {
		if errors.Is(err, flag.ErrHelp) {
			return 0
		}
		return 2
	}
	if flags.NArg() > 0 {
		fmt.Fprintf(stderr, "{{ npm_name }}: unexpected argument %q\n", flags.Arg(0))
		return 2
	}

	data, err := readInput(*path, stdin)
	if err != nil {
		fmt.Fprintf(stderr, "{{ npm_name }}: %v\n", err)
		return 1
	}
	urls, err := Parse(data)
	if err != nil {
		fmt.Fprintf(stderr, "{{ npm_name }}: %v\n", err)
		return 1
	}
	if *render {
		document, err := Render(urls)
		if err != nil {
			fmt.Fprintf(stderr, "{{ npm_name }}: %v\n", err)
			return 1
		}
		fmt.Fprint(stdout, document)
		return 0
	}
	fmt.Fprintf(stdout, "urls=%d\n", len(urls))
	return 0
}

func readInput(path string, stdin io.Reader) ([]byte, error) {
	if path == "" {
		return io.ReadAll(stdin)
	}
	return os.ReadFile(path)
}
