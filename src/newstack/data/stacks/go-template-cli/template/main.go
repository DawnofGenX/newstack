package main

import (
	"flag"
	"fmt"
	"os"
)

const usageText = `usage: %s -template FILE [-data FILE] [-out FILE]

Renders a text/template file against a JSON document. Without -data the
template runs against an empty object; without -out the result goes to stdout.
An unknown key is an error, so a typo in {{! .Name }} fails instead of printing
"<no value>".
`

func run(args []string, stdout, stderr *os.File) int {
	flags := flag.NewFlagSet("{{ npm_name }}", flag.ContinueOnError)
	flags.SetOutput(stderr)
	templatePath := flags.String("template", "", "template file")
	dataPath := flags.String("data", "", "JSON data file")
	outPath := flags.String("out", "", "write the result here instead of stdout")
	if err := flags.Parse(args); err != nil {
		return 2
	}
	if *templatePath == "" {
		fmt.Fprintf(stderr, usageText, "{{ npm_name }}")
		return 2
	}
	data := map[string]any{}
	if *dataPath != "" {
		raw, err := os.ReadFile(*dataPath)
		if err != nil {
			fmt.Fprintf(stderr, "data: %v\n", err)
			return 1
		}
		decoded, err := DecodeData(raw)
		if err != nil {
			fmt.Fprintf(stderr, "%v\n", err)
			return 1
		}
		data = decoded
	}
	out := stdout
	if *outPath != "" {
		file, err := os.Create(*outPath)
		if err != nil {
			fmt.Fprintf(stderr, "out: %v\n", err)
			return 1
		}
		defer func() { _ = file.Close() }()
		out = file
	}
	if err := RenderFile(*templatePath, out, data); err != nil {
		fmt.Fprintf(stderr, "%v\n", err)
		return 1
	}
	return 0
}

func main() {
	os.Exit(run(os.Args[1:], os.Stdout, os.Stderr))
}
