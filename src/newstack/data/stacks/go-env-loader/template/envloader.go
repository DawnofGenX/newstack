package main

import (
	"encoding/json"
	"fmt"
	"os"
	"sort"
	"strings"
)

// ParseDotEnv parses .env formatted content into a map.
func ParseDotEnv(content string) map[string]string {
	out := map[string]string{}
	for _, raw := range strings.Split(content, "\n") {
		line := strings.TrimSpace(raw)
		if line == "" {
			continue
		}
		if strings.HasPrefix(line, "#") {
			continue
		}
		if strings.HasPrefix(line, "export ") {
			line = strings.TrimSpace(strings.TrimPrefix(line, "export "))
		}
		idx := strings.IndexByte(line, '=')
		if idx < 0 {
			continue
		}
		key := strings.TrimSpace(line[:idx])
		val := strings.TrimSpace(line[idx+1:])
		if key == "" {
			continue
		}
		if len(val) >= 2 {
			if (val[0] == '"' && val[len(val)-1] == '"') || (val[0] == '\'' && val[len(val)-1] == '\'') {
				val = val[1 : len(val)-1]
			} else {
				// strip inline comment
				if i := strings.Index(val, " #"); i >= 0 {
					val = strings.TrimSpace(val[:i])
				}
			}
		} else {
			if i := strings.Index(val, " #"); i >= 0 {
				val = strings.TrimSpace(val[:i])
			}
		}
		out[key] = val
	}
	return out
}

// Resolve merges layers in order; later layers override earlier ones.
func Resolve(layers ...map[string]string) map[string]string {
	out := map[string]string{}
	for _, l := range layers {
		for k, v := range l {
			out[k] = v
		}
	}
	return out
}

func main() {
	file := ""
	override := ""
	for i := 1; i < len(os.Args); i++ {
		if os.Args[i] == "-file" && i+1 < len(os.Args) {
			file = os.Args[i+1]
			i++
		} else if os.Args[i] == "-set" && i+1 < len(os.Args) {
			override = os.Args[i+1]
			i++
		}
	}
	layers := []map[string]string{}
	if file != "" {
		b, err := os.ReadFile(file)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		layers = append(layers, ParseDotEnv(string(b)))
	}
	if override != "" {
		// KEY=VAL
		if idx := strings.IndexByte(override, '='); idx >= 0 {
			k := strings.TrimSpace(override[:idx])
			v := strings.TrimSpace(override[idx+1:])
			layers = append(layers, map[string]string{k: v})
		}
	}
	resolved := Resolve(layers...)
	// include process env? only if -env flag; simple: no.
	keys := make([]string, 0, len(resolved))
	for k := range resolved {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	ordered := map[string]string{}
	for _, k := range keys {
		ordered[k] = resolved[k]
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	enc.Encode(ordered)
}