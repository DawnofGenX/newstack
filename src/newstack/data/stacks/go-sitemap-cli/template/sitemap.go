package main

import (
	"encoding/xml"
	"errors"
	"fmt"
	"strconv"
	"strings"
	"time"
)

// Namespace is the sitemap protocol namespace every document must declare.
const Namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"

var changeFreqs = map[string]bool{
	"always": true, "hourly": true, "daily": true, "weekly": true,
	"monthly": true, "yearly": true, "never": true,
}

// URL is one <url> entry in a sitemap document.
type URL struct {
	Loc        string `xml:"loc"`
	LastMod    string `xml:"lastmod,omitempty"`
	ChangeFreq string `xml:"changefreq,omitempty"`
	Priority   string `xml:"priority,omitempty"`
}

type urlset struct {
	XMLName xml.Name `xml:"urlset"`
	Xmlns   string   `xml:"xmlns,attr,omitempty"`
	URLs    []URL    `xml:"url"`
}

// Validate reports the first problem with a single entry.
func Validate(entry URL) error {
	loc := strings.TrimSpace(entry.Loc)
	if loc == "" {
		return errors.New("loc is required")
	}
	if !strings.HasPrefix(loc, "http://") && !strings.HasPrefix(loc, "https://") {
		return fmt.Errorf("loc must be an absolute http(s) URL: %q", entry.Loc)
	}
	if strings.ContainsAny(loc, " \t\r\n") {
		return fmt.Errorf("loc must not contain whitespace: %q", entry.Loc)
	}
	if entry.LastMod != "" {
		if _, err := parseLastMod(entry.LastMod); err != nil {
			return err
		}
	}
	if entry.ChangeFreq != "" && !changeFreqs[entry.ChangeFreq] {
		return fmt.Errorf("unknown changefreq %q (want always, hourly, daily, weekly, monthly, yearly or never)", entry.ChangeFreq)
	}
	if entry.Priority != "" {
		value, err := strconv.ParseFloat(entry.Priority, 64)
		if err != nil {
			return fmt.Errorf("priority must be a number: %q", entry.Priority)
		}
		if value < 0 || value > 1 {
			return fmt.Errorf("priority must be between 0.0 and 1.0: %q", entry.Priority)
		}
	}
	return nil
}

func parseLastMod(text string) (time.Time, error) {
	for _, layout := range []string{time.RFC3339, "2006-01-02"} {
		if parsed, err := time.Parse(layout, text); err == nil {
			return parsed, nil
		}
	}
	return time.Time{}, fmt.Errorf("lastmod must be an RFC 3339 timestamp or a YYYY-MM-DD date: %q", text)
}

// Render validates every entry and returns the sitemap document.
func Render(urls []URL) (string, error) {
	if len(urls) == 0 {
		return "", errors.New("a sitemap needs at least one url")
	}
	for index, entry := range urls {
		if err := Validate(entry); err != nil {
			return "", fmt.Errorf("url %d: %w", index+1, err)
		}
	}
	document := urlset{Xmlns: Namespace, URLs: urls}
	body, err := xml.MarshalIndent(document, "", "  ")
	if err != nil {
		return "", err
	}
	return xml.Header + string(body) + "\n", nil
}

// Parse reads a sitemap document and returns its entries.
func Parse(data []byte) ([]URL, error) {
	var document urlset
	if err := xml.Unmarshal(data, &document); err != nil {
		return nil, fmt.Errorf("not a sitemap: %w", err)
	}
	if document.XMLName.Local != "urlset" {
		return nil, fmt.Errorf("root element must be <urlset>, got <%s>", document.XMLName.Local)
	}
	if len(document.URLs) == 0 {
		return nil, errors.New("sitemap has no <url> entries")
	}
	for index, entry := range document.URLs {
		if err := Validate(entry); err != nil {
			return nil, fmt.Errorf("url %d: %w", index+1, err)
		}
	}
	return document.URLs, nil
}
