package main

import (
	"bytes"
	"strings"
	"testing"
)

const sample = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/?a=1&amp;b=2</loc>
    <lastmod>2024-05-01</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://example.com/about</loc>
  </url>
</urlset>
`

func TestValidateAcceptsACompleteEntry(t *testing.T) {
	entry := URL{Loc: "https://example.com/", LastMod: "2024-05-01", ChangeFreq: "daily", Priority: "0.5"}
	if err := Validate(entry); err != nil {
		t.Fatalf("expected a clean entry, got %v", err)
	}
}

func TestValidateRejectsBadEntries(t *testing.T) {
	cases := []struct {
		name  string
		entry URL
		want  string
	}{
		{"missing loc", URL{}, "loc is required"},
		{"relative loc", URL{Loc: "/about"}, "absolute http(s) URL"},
		{"whitespace in loc", URL{Loc: "https://example.com/a b"}, "must not contain whitespace"},
		{"bad lastmod", URL{Loc: "https://example.com/", LastMod: "01/05/2024"}, "lastmod must be"},
		{"bad changefreq", URL{Loc: "https://example.com/", ChangeFreq: "sometimes"}, "unknown changefreq"},
		{"priority above one", URL{Loc: "https://example.com/", Priority: "1.5"}, "between 0.0 and 1.0"},
		{"priority not a number", URL{Loc: "https://example.com/", Priority: "high"}, "must be a number"},
	}
	for _, testCase := range cases {
		t.Run(testCase.name, func(t *testing.T) {
			err := Validate(testCase.entry)
			if err == nil || !strings.Contains(err.Error(), testCase.want) {
				t.Fatalf("want an error containing %q, got %v", testCase.want, err)
			}
		})
	}
}

func TestParseReadsEntriesAndUnescapesLoc(t *testing.T) {
	urls, err := Parse([]byte(sample))
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if len(urls) != 2 {
		t.Fatalf("want 2 urls, got %d", len(urls))
	}
	if urls[0].Loc != "https://example.com/?a=1&b=2" {
		t.Fatalf("unescaped loc mismatch: %q", urls[0].Loc)
	}
	if urls[0].ChangeFreq != "weekly" || urls[0].Priority != "0.8" || urls[0].LastMod != "2024-05-01" {
		t.Fatalf("fields not parsed: %+v", urls[0])
	}
}

func TestParseRejectsNonSitemapInput(t *testing.T) {
	if _, err := Parse([]byte("not xml")); err == nil {
		t.Fatal("expected an error for non-XML input")
	}
	if _, err := Parse([]byte(`<rss></rss>`)); err == nil || !strings.Contains(err.Error(), "urlset") {
		t.Fatalf("want a root element error, got %v", err)
	}
	if _, err := Parse([]byte(`<urlset></urlset>`)); err == nil || !strings.Contains(err.Error(), "no <url> entries") {
		t.Fatalf("want the empty sitemap error, got %v", err)
	}
}

func TestRenderRoundTripsThroughParse(t *testing.T) {
	urls, err := Parse([]byte(sample))
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	document, err := Render(urls)
	if err != nil {
		t.Fatalf("render failed: %v", err)
	}
	if !strings.HasPrefix(document, `<?xml version="1.0" encoding="UTF-8"?>`) {
		t.Fatalf("missing XML header: %q", document[:40])
	}
	if !strings.Contains(document, `xmlns="`+Namespace+`"`) {
		t.Fatalf("missing namespace: %s", document)
	}
	if !strings.Contains(document, "https://example.com/?a=1&amp;b=2") {
		t.Fatalf("loc was not escaped: %s", document)
	}
	again, err := Parse([]byte(document))
	if err != nil {
		t.Fatalf("re-parse failed: %v", err)
	}
	if len(again) != len(urls) || again[1].Loc != urls[1].Loc {
		t.Fatalf("round trip changed the document: %+v", again)
	}
}

func TestRenderRefusesAnEmptyList(t *testing.T) {
	if _, err := Render(nil); err == nil {
		t.Fatal("expected an error for an empty sitemap")
	}
}

func TestRunPrintsTheURLCount(t *testing.T) {
	var stdout, stderr bytes.Buffer
	code := run(nil, strings.NewReader(sample), &stdout, &stderr)
	if code != 0 {
		t.Fatalf("want exit 0, got %d (%s)", code, stderr.String())
	}
	if stdout.String() != "urls=2\n" {
		t.Fatalf("unexpected output %q", stdout.String())
	}
}

func TestRunRendersWhenAsked(t *testing.T) {
	var stdout, stderr bytes.Buffer
	code := run([]string{"-render"}, strings.NewReader(sample), &stdout, &stderr)
	if code != 0 {
		t.Fatalf("want exit 0, got %d (%s)", code, stderr.String())
	}
	if !strings.Contains(stdout.String(), "<changefreq>weekly</changefreq>") {
		t.Fatalf("render output missing fields: %s", stdout.String())
	}
}

func TestRunReportsBadInputWithExitOne(t *testing.T) {
	var stdout, stderr bytes.Buffer
	code := run([]string{"-file", "/nonexistent/sitemap.xml"}, strings.NewReader(""), &stdout, &stderr)
	if code != 1 {
		t.Fatalf("want exit 1, got %d", code)
	}
	if !strings.Contains(stderr.String(), "no such file") {
		t.Fatalf("unexpected stderr %q", stderr.String())
	}
}

func TestRunRejectsUnknownFlagsWithExitTwo(t *testing.T) {
	var stdout, stderr bytes.Buffer
	code := run([]string{"--bogus"}, strings.NewReader(sample), &stdout, &stderr)
	if code != 2 {
		t.Fatalf("want exit 2, got %d", code)
	}
}
