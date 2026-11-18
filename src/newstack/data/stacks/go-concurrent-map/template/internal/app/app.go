package app

import (
	"fmt"
	"io"

	"{{ npm_name }}/internal/cmap"
)

func Run(args []string, stdin io.Reader, stdout, stderr io.Writer) int {
	m := cmap.New[string, int]()
	m.Set("a", 1)
	m.Set("b", 2)
	m.Set("c", 3)
	if v, ok := m.Get("b"); !ok || v != 2 {
		fmt.Fprintln(stderr, "get failed")
		return 1
	}
	m.Delete("c")
	fmt.Fprintf(stdout, "size=%d\n", m.Len())
	return 0
}
