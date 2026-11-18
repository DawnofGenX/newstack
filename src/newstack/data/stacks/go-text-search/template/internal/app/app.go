package app

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"strings"

	"{{ npm_name }}/internal/search"
)

func Run(args []string, stdin io.Reader, stdout, stderr io.Writer) int {
	if len(args) < 2 {
		fmt.Fprintln(stderr, "usage: text-search PATTERN FILE")
		return 2
	}
	pattern := args[0]
	path := args[1]
	var data []byte
	var err error
	if path == "-" {
		r := bufio.NewReader(stdin)
		data, err = io.ReadAll(r)
	} else {
		data, err = os.ReadFile(path)
	}
	if err != nil {
		fmt.Fprintf(stderr, "read error: %v\n", err)
		return 1
	}
	text := string(data)
	lines := strings.Split(text, "\n")
	matches := search.Search(text, pattern)
	if len(matches) == 0 {
		fmt.Fprintln(stdout, "no matches")
		return 0
	}
	for _, m := range matches {
		lineText := ""
		if m.Line-1 < len(lines) {
			lineText = lines[m.Line-1]
		}
		if path == "-" {
			fmt.Fprintf(stdout, "%d:%d: %s\n", m.Line, m.Column, lineText)
		} else {
			fmt.Fprintf(stdout, "%s:%d:%d: %s\n", path, m.Line, m.Column, lineText)
		}
	}
	return 0
}
