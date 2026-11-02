// Package app holds the command implementation so it can be tested without
// building or running a binary.
package app

import (
	"errors"
	"flag"
	"fmt"
	"io"
)

// Version is the released version of the tool, reported by --version.
const Version = "0.1.0"

const usage = `Usage: {{ npm_name }} <command> [flags]

Commands:
  greet    Print a greeting

Flags:
  --version    Print the version and exit
  --help       Print this help and exit
`

// Run executes the command described by args and returns a process exit code.
// Output is written to stdout, diagnostics to stderr, which keeps the command
// testable with plain buffers.
func Run(args []string, stdout, stderr io.Writer) int {
	if len(args) == 0 {
		fmt.Fprint(stderr, usage)
		return 2
	}

	switch args[0] {
	case "greet":
		return runGreet(args[1:], stdout, stderr)
	case "--version", "-version", "version":
		fmt.Fprintln(stdout, Version)
		return 0
	case "--help", "-h", "-help", "help":
		fmt.Fprint(stdout, usage)
		return 0
	default:
		fmt.Fprintf(stderr, "unknown command %q\n\n%s", args[0], usage)
		return 2
	}
}

func runGreet(args []string, stdout, stderr io.Writer) int {
	fs := flag.NewFlagSet("greet", flag.ContinueOnError)
	fs.SetOutput(stderr)
	fs.Usage = func() { fmt.Fprint(stderr, usage) }

	name := fs.String("name", "world", "who to greet")

	if err := fs.Parse(args); err != nil {
		if errors.Is(err, flag.ErrHelp) {
			return 0
		}
		return 2
	}
	if fs.NArg() > 0 {
		fmt.Fprintf(stderr, "unexpected argument %q\n", fs.Arg(0))
		return 2
	}

	fmt.Fprintf(stdout, "Hello, %s!\n", *name)
	return 0
}
