package main

import (
	"fmt"
	"os"
)

func usage() {
	fmt.Fprintln(os.Stderr, "usage: app compare <a> <b> | app satisfies <version> <constraint>")
	os.Exit(2)
}

func main() {
	args := os.Args[1:]
	if len(args) < 3 {
		usage()
	}
	switch args[0] {
	case "compare":
		a, err := Parse(args[1])
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		b, err := Parse(args[2])
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		fmt.Println(Compare(a, b))
	case "satisfies":
		v, err := Parse(args[1])
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		ok, err := Satisfies(v, args[2])
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		fmt.Println(ok)
	default:
		usage()
	}
}
