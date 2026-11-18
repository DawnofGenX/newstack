// Package main renders a text/template file against a JSON document.
//
// The renderer is strict on purpose: an unknown key is an error rather than the
// "<no value>" that hides a typo until the output reaches production, and the
// helper functions cover the formatting that templates otherwise end up doing
// with a chain of printf verbs.
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"sort"
	"strings"
	"text/template"
)

// Funcs are the helpers a template may call.
var Funcs = template.FuncMap{
	"upper":   strings.ToUpper,
	"lower":   strings.ToLower,
	"title":   func(s string) string { return strings.Title(strings.ToLower(s)) }, //nolint:staticcheck
	"trim":    strings.TrimSpace,
	"replace": func(old, new, s string) string { return strings.ReplaceAll(s, old, new) },
	"repeat":  func(count int, s string) string { return strings.Repeat(s, count) },
	"join":    func(sep string, items []string) string { return strings.Join(items, sep) },
	"indent": func(width int, s string) string {
		pad := strings.Repeat(" ", width)
		lines := strings.Split(s, "\n")
		for index, line := range lines {
			if line != "" {
				lines[index] = pad + line
			}
		}
		return strings.Join(lines, "\n")
	},
	"json": func(value any) (string, error) {
		encoded, err := json.Marshal(value)
		return string(encoded), err
	},
	"keys": func(value map[string]any) []string {
		out := make([]string, 0, len(value))
		for key := range value {
			out = append(out, key)
		}
		sort.Strings(out)
		return out
	},
	"default": func(fallback, value any) any {
		if value == nil {
			return fallback
		}
		if text, ok := value.(string); ok && text == "" {
			return fallback
		}
		return value
	},
}

// Render executes template text with data, failing on an unknown key.
func Render(text string, data map[string]any, out io.Writer) error {
	parsed, err := template.New("template").Option("missingkey=error").Funcs(Funcs).Parse(text)
	if err != nil {
		return fmt.Errorf("template: %w", err)
	}
	if err := parsed.Execute(out, data); err != nil {
		return fmt.Errorf("render: %w", err)
	}
	return nil
}

// DecodeData turns a JSON document into the map a template indexes into.
func DecodeData(raw []byte) (map[string]any, error) {
	var data map[string]any
	if len(strings.TrimSpace(string(raw))) == 0 {
		return map[string]any{}, nil
	}
	if err := json.Unmarshal(raw, &data); err != nil {
		return nil, fmt.Errorf("data: %w", err)
	}
	return data, nil
}

// RenderFile reads the template from disk and renders it to out.
func RenderFile(path string, out io.Writer, data map[string]any) error {
	raw, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("template: %w", err)
	}
	return Render(string(raw), data, out)
}
