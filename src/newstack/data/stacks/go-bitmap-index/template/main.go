package main

import (
	"bufio"
	"flag"
	"fmt"
	"io"
	"os"
	"strconv"
	"strings"
)

func main() {
	size := flag.Int("size", 1024, "number of addressable bits")
	file := flag.String("file", "-", "file of integers, one per line (- reads stdin)")
	query := flag.String("query", "", "comma separated rank=N,select=N,has=N")
	flag.Parse()

	bitmap := NewBitmap(*size)
	var reader io.Reader = os.Stdin
	if *file != "-" {
		handle, err := os.Open(*file)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		defer handle.Close()
		reader = handle
	}
	scanner := bufio.NewScanner(reader)
	for scanner.Scan() {
		text := strings.TrimSpace(scanner.Text())
		if text == "" {
			continue
		}
		value, err := strconv.Atoi(text)
		if err != nil {
			fmt.Fprintf(os.Stderr, "not an integer: %s\n", text)
			os.Exit(1)
		}
		if !bitmap.Set(value) {
			fmt.Fprintf(os.Stderr, "value %d is outside size %d\n", value, *size)
			os.Exit(1)
		}
	}
	fmt.Printf("size=%d set=%d bits=%d\n", *size, bitmap.Count(), bitmap.Len())

	for _, item := range strings.Split(*query, ",") {
		item = strings.TrimSpace(item)
		if item == "" {
			continue
		}
		parts := strings.SplitN(item, "=", 2)
		if len(parts) != 2 {
			fmt.Fprintf(os.Stderr, "bad query %q\n", item)
			os.Exit(2)
		}
		value, err := strconv.Atoi(parts[1])
		if err != nil {
			fmt.Fprintf(os.Stderr, "bad query %q\n", item)
			os.Exit(2)
		}
		switch parts[0] {
		case "rank":
			fmt.Printf("rank(%d)=%d\n", value, bitmap.Rank(value))
		case "select":
			fmt.Printf("select(%d)=%d\n", value, bitmap.Select(value))
		case "has":
			fmt.Printf("has(%d)=%v\n", value, bitmap.Has(value))
		default:
			fmt.Fprintf(os.Stderr, "unknown query %q\n", parts[0])
			os.Exit(2)
		}
	}
}
