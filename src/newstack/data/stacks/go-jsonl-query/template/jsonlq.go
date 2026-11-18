package main

import (
	"bufio"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"strconv"
	"strings"
)

// Options controls a query run.
type Options struct {
	Select []string
	Where  string
	Count  bool
}

// StreamQuery reads JSONL from r, applies filtering/selection, writes to w.
func StreamQuery(r io.Reader, w io.Writer, opts Options) error {
	scanner := bufio.NewScanner(r)
	scanner.Buffer(make([]byte, 1024*1024), 1024*1024)
	enc := json.NewEncoder(w)
	count := 0
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}
		var obj map[string]any
		if err := json.Unmarshal([]byte(line), &obj); err != nil {
			return fmt.Errorf("invalid json: %w", err)
		}
		if !matchWhere(obj, opts.Where) {
			continue
		}
		if opts.Count {
			count++
			continue
		}
		out := obj
		if len(opts.Select) > 0 {
			out = map[string]any{}
			for _, f := range opts.Select {
				if v, ok := obj[f]; ok {
					out[f] = v
				}
			}
		}
		if err := enc.Encode(out); err != nil {
			return err
		}
	}
	if opts.Count {
		fmt.Fprintln(w, count)
	}
	return scanner.Err()
}

func matchWhere(obj map[string]any, where string) bool {
	where = strings.TrimSpace(where)
	if where == "" {
		return true
	}
	op, field, val, ok := parseWhere(where)
	if !ok {
		return false
	}
	actual, present := obj[field]
	if !present {
		return false
	}
	return compare(actual, val, op)
}

func parseWhere(where string) (op, field, val string, ok bool) {
	ops := []string{"==", "!=", ">=", "<=", ">", "<", "="}
	for _, o := range ops {
		// find operator not inside? simple split
		if idx := indexOfOp(where, o); idx >= 0 {
			field = strings.TrimSpace(where[:idx])
			val = strings.TrimSpace(where[idx+len(o):])
			op = o
			if op == "=" {
				op = "=="
			}
			return op, field, val, true
		}
	}
	return "", "", "", false
}

func indexOfOp(s, op string) int {
	// find op allowing no spaces; ensure field present
	i := strings.Index(s, op)
	return i
}

func compare(actual any, val string, op string) bool {
	// try numeric
	an, aNum := toFloat(actual)
	vn, vNum := toFloatStr(val)
	if aNum && vNum {
		switch op {
		case "==":
			return an == vn
		case "!=":
			return an != vn
		case ">":
			return an > vn
		case "<":
			return an < vn
		case ">=":
			return an >= vn
		case "<=":
			return an <= vn
		}
	}
	as := fmt.Sprintf("%v", actual)
	switch op {
	case "==":
		return as == val
	case "!=":
		return as != val
	case ">":
		return as > val
	case "<":
		return as < val
	case ">=":
		return as >= val
	case "<=":
		return as <= val
	}
	return false
}

func toFloat(v any) (float64, bool) {
	switch t := v.(type) {
	case float64:
		return t, true
	case int:
		return float64(t), true
	case json.Number:
		f, err := t.Float64()
		return f, err == nil
	}
	return 0, false
}

func toFloatStr(s string) (float64, bool) {
	f, err := strconv.ParseFloat(s, 64)
	return f, err == nil
}

func main() {
	fs := flag.NewFlagSet("jsonlq", flag.ExitOnError)
	file := fs.String("file", "", "input JSONL file (default stdin)")
	selectFlag := fs.String("select", "", "comma-separated fields to select")
	whereFlag := fs.String("where", "", "filter expression field=value")
	countFlag := fs.Bool("count", false, "print count of matching records")
	_ = fs.Parse(os.Args[1:])

	opts := Options{Where: *whereFlag, Count: *countFlag}
	if *selectFlag != "" {
		for _, f := range strings.Split(*selectFlag, ",") {
			f = strings.TrimSpace(f)
			if f != "" {
				opts.Select = append(opts.Select, f)
			}
		}
	}

	var r io.Reader = os.Stdin
	if *file != "" {
		f, err := os.Open(*file)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		defer f.Close()
		r = f
	}
	if err := StreamQuery(r, os.Stdout, opts); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
