package app

import (
	"bufio"
	"fmt"
	"io"
	"strconv"
	"strings"

	"{{ npm_name }}/internal/pq"
)

func Run(args []string, stdin io.Reader, stdout, stderr io.Writer) int {
	q := pq.New()
	scanner := bufio.NewScanner(stdin)
	scanner.Buffer(make([]byte, 1024*1024), 1024*1024)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}
		fields := strings.Fields(line)
		prio := 0
		value := ""
		idx := 0
		if len(fields) >= 1 {
			// support optional leading verb
			if fields[0] == "add" || fields[0] == "task" || fields[0] == "push" {
				idx = 1
			}
		}
		if idx >= len(fields) {
			fmt.Fprintf(stderr, "bad line: %s\n", line)
			return 2
		}
		n, err := strconv.Atoi(fields[idx])
		if err != nil {
			fmt.Fprintf(stderr, "bad priority in: %s\n", line)
			return 2
		}
		prio = n
		rest := fields[idx+1:]
		if len(rest) == 0 {
			fmt.Fprintf(stderr, "missing task name: %s\n", line)
			return 2
		}
		value = strings.Join(rest, " ")
		q.Push(prio, value)
	}
	// schedule output
	for q.Len() > 0 {
		p, v, _ := q.Pop()
		fmt.Fprintf(stdout, "%d %s\n", p, v)
	}
	return 0
}
