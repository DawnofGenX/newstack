package main

import (
	"flag"
	"fmt"
	"io"
	"os"
)

const usage = `usage: %s <command> [options]

commands:
  det        determinant of a square matrix        (-file)
  trace      sum of the main diagonal              (-file)
  transpose  swap rows and columns                 (-file)
  mul        matrix product                        (-file, -with)
  identity   n x n identity matrix                 (-size)

options:
  -file <path>   read the matrix from a JSON file (default: stdin)
  -with <path>   right-hand matrix for mul
  -size <n>      identity size (default 3)
  -h             show this help
`

type failure int

const (
	noFailure failure = iota
	inputFailure
	usageFailure
)

func readMatrix(path string, stdin io.Reader) (Matrix, error) {
	var (
		raw []byte
		err error
	)
	if path == "" {
		raw, err = io.ReadAll(stdin)
	} else {
		raw, err = os.ReadFile(path)
	}
	if err != nil {
		return Matrix{}, fmt.Errorf("cannot read %s: %v", path, err)
	}
	return ParseMatrix(string(raw))
}

// run executes one command and returns the process exit code.
func run(args []string, stdin io.Reader, stdout, stderr io.Writer) int {
	if len(args) == 0 {
		fmt.Fprintf(stderr, "matrix: a command is required\n")
		fmt.Fprintf(stderr, usage, "matrix")
		return int(usageFailure)
	}
	command := args[0]
	set := flag.NewFlagSet(command, flag.ContinueOnError)
	set.SetOutput(stderr)
	file := set.String("file", "", "matrix file")
	with := set.String("with", "", "right-hand matrix for mul")
	size := set.Int("size", 3, "identity size")
	if err := set.Parse(args[1:]); err != nil {
		return int(usageFailure)
	}
	if set.NArg() > 0 {
		fmt.Fprintf(stderr, "matrix: unexpected argument %q\n", set.Arg(0))
		return int(usageFailure)
	}

	known := map[string]bool{"det": true, "trace": true, "transpose": true, "mul": true, "identity": true}
	if !known[command] {
		fmt.Fprintf(stderr, "matrix: unknown command %q\n", command)
		fmt.Fprintf(stderr, usage, "matrix")
		return int(usageFailure)
	}

	if command == "identity" {
		identity, err := Identity(*size)
		if err != nil {
			fmt.Fprintf(stderr, "matrix: %v\n", err)
			return int(inputFailure)
		}
		fmt.Fprintln(stdout, identity.Describe())
		return int(noFailure)
	}

	matrix, err := readMatrix(*file, stdin)
	if err != nil {
		fmt.Fprintf(stderr, "matrix: %v\n", err)
		return int(inputFailure)
	}

	switch command {
	case "det":
		value, err := matrix.Determinant()
		if err != nil {
			fmt.Fprintf(stderr, "matrix: %v\n", err)
			return int(inputFailure)
		}
		fmt.Fprintf(stdout, "det=%s\n", FormatNumber(value))
	case "trace":
		value, err := matrix.Trace()
		if err != nil {
			fmt.Fprintf(stderr, "matrix: %v\n", err)
			return int(inputFailure)
		}
		fmt.Fprintf(stdout, "trace=%s\n", FormatNumber(value))
	case "transpose":
		fmt.Fprintln(stdout, matrix.Transpose().Describe())
	case "mul":
		if *with == "" {
			fmt.Fprintf(stderr, "matrix: mul needs -with <path>\n")
			return int(usageFailure)
		}
		right, err := readMatrix(*with, stdin)
		if err != nil {
			fmt.Fprintf(stderr, "matrix: %v\n", err)
			return int(inputFailure)
		}
		product, err := Multiply(matrix, right)
		if err != nil {
			fmt.Fprintf(stderr, "matrix: %v\n", err)
			return int(inputFailure)
		}
		fmt.Fprintln(stdout, product.Describe())
	default:
		// Unreachable: the command name is validated before any input is read.
		return int(usageFailure)
	}
	return int(noFailure)
}

func main() {
	if len(os.Args) > 1 && (os.Args[1] == "-h" || os.Args[1] == "--help" || os.Args[1] == "help") {
		fmt.Printf(usage, "{{ npm_name }}")
		return
	}
	os.Exit(run(os.Args[1:], os.Stdin, os.Stdout, os.Stderr))
}
