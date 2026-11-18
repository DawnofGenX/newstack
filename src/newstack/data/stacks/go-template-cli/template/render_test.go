package main

import (
	"bytes"
	"strings"
	"testing"
)

func render(t *testing.T, text string, data map[string]any) string {
	t.Helper()
	var buf bytes.Buffer
	if err := Render(text, data, &buf); err != nil {
		t.Fatalf("Render failed: %v", err)
	}
	return buf.String()
}

func TestPlainField(t *testing.T) {
	if got := render(t, "hello {{! .Name }}", map[string]any{"Name": "ada"}); got != "hello ada" {
		t.Fatalf("got %q", got)
	}
}

func TestUnknownKeyIsAnError(t *testing.T) {
	var buf bytes.Buffer
	err := Render("{{! .Missing }}", map[string]any{}, &buf)
	if err == nil || !strings.Contains(err.Error(), "map has no entry for key") {
		t.Fatalf("expected a missing key error, got %v", err)
	}
}

func TestNestedFieldsAndRanges(t *testing.T) {
	data := map[string]any{
		"services": []any{
			map[string]any{"name": "api", "port": 8080.0},
			map[string]any{"name": "db", "port": 5432.0},
		},
	}
	got := render(t, `{{! range .services }}{{! .name }}={{! .port }} {{! end }}`, data)
	if strings.TrimSpace(got) != "api=8080 db=5432" {
		t.Fatalf("got %q", got)
	}
}

func TestCaseHelpers(t *testing.T) {
	got := render(t, "{{! upper .x }}|{{! lower .y }}", map[string]any{"x": "abc", "y": "DEF"})
	if got != "ABC|def" {
		t.Fatalf("got %q", got)
	}
}

func TestDefaultReplacesAnEmptyString(t *testing.T) {
	got := render(t, "{{! default \"guest\" .user }}", map[string]any{"user": ""})
	if got != "guest" {
		t.Fatalf("got %q", got)
	}
}

func TestRepeatAndJoin(t *testing.T) {
	got := render(t, "{{! repeat 3 \"ab\" }}{{! join \",\" .tags }}", map[string]any{"tags": []string{"x", "y"}})
	if got != "abababx,y" {
		t.Fatalf("got %q", got)
	}
}

func TestIndentSkipsBlankLines(t *testing.T) {
	got := render(t, "{{! indent 2 .body }}", map[string]any{"body": "one\n\ntwo"})
	if got != "  one\n\n  two" {
		t.Fatalf("got %q", got)
	}
}

func TestJSONHelperQuotesItsValue(t *testing.T) {
	got := render(t, "{{! json .list }}", map[string]any{"list": []string{"a"}})
	if got != `["a"]` {
		t.Fatalf("got %q", got)
	}
}

func TestKeysAreSorted(t *testing.T) {
	got := render(t, "{{! join \",\" (keys .m) }}", map[string]any{"m": map[string]any{"b": 1, "a": 2}})
	if got != "a,b" {
		t.Fatalf("got %q", got)
	}
}

func TestParseErrorMentionsTheTemplate(t *testing.T) {
	var buf bytes.Buffer
	err := Render("{{! if }}", map[string]any{}, &buf)
	if err == nil || !strings.HasPrefix(err.Error(), "template: ") {
		t.Fatalf("expected a template parse error, got %v", err)
	}
}

func TestDecodeDataAcceptsEmptyInput(t *testing.T) {
	data, err := DecodeData([]byte("  \n"))
	if err != nil {
		t.Fatalf("empty input must be allowed: %v", err)
	}
	if len(data) != 0 {
		t.Fatalf("expected an empty map, got %v", data)
	}
}

func TestDecodeDataRejectsBrokenJSON(t *testing.T) {
	if _, err := DecodeData([]byte("{")); err == nil {
		t.Fatal("broken JSON must fail")
	}
}
