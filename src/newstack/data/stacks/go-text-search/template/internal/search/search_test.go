package search

import "testing"

func TestBasic(t *testing.T) {
	text := "hello world\nhello go\n"
	matches := Search(text, "hello")
	if len(matches) != 2 {
		t.Fatalf("got %d", len(matches))
	}
	if matches[0].Line != 1 || matches[0].Column != 1 {
		t.Fatalf("first wrong: %+v", matches[0])
	}
	if matches[1].Line != 2 || matches[1].Column != 1 {
		t.Fatalf("second wrong: %+v", matches[1])
	}
}

func TestColumn(t *testing.T) {
	text := "abc needle xyz\n"
	matches := Search(text, "needle")
	if len(matches) != 1 {
		t.Fatalf("got %d", len(matches))
	}
	if matches[0].Column != 5 {
		t.Fatalf("col wrong: %d", matches[0].Column)
	}
}

func TestNotFound(t *testing.T) {
	if len(Search("abc", "zzz")) != 0 {
		t.Fatal("expected none")
	}
}

func TestOverlapping(t *testing.T) {
	if len(Search("aaaa", "aa")) != 3 {
		t.Fatalf("got %d", len(Search("aaaa", "aa")))
	}
}
