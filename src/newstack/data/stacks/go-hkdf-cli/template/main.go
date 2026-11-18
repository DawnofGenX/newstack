package main

import (
	"fmt"
	"io"
	"os"
	"strings"
)

func main() {
	stdin, _ := io.ReadAll(os.Stdin)
	out, err := run(os.Args[1:], stdin)
	if err != nil {
		message := err.Error()
		switch {
		case strings.HasPrefix(message, "unknown option"),
			strings.HasPrefix(message, "option "),
			strings.HasPrefix(message, "length must be"),
			strings.HasPrefix(message, "only one input"):
			fmt.Fprintln(os.Stderr, "error: "+message)
			fmt.Fprintln(os.Stderr, usage())
			os.Exit(2)
		default:
			fmt.Fprintln(os.Stderr, "error: "+message)
			os.Exit(1)
		}
	}
	fmt.Println(out)
}
