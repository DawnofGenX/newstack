package main

import (
	"strings"
	"testing"
	"time"
)

func mustParse(t *testing.T, spec string) *Schedule {
	t.Helper()
	schedule, err := Parse(spec)
	if err != nil {
		t.Fatalf("Parse(%q) failed: %v", spec, err)
	}
	return schedule
}

func mustTime(t *testing.T, text string) time.Time {
	t.Helper()
	parsed, err := time.Parse(time.RFC3339, text)
	if err != nil {
		t.Fatalf("bad fixture %q: %v", text, err)
	}
	return parsed
}

func TestParseRejectsWrongFieldCount(t *testing.T) {
	if _, err := Parse("* * * *"); err == nil {
		t.Fatal("a four field expression must fail")
	}
}

func TestParseRejectsOutOfRange(t *testing.T) {
	_, err := Parse("61 * * * *")
	if err == nil || !strings.Contains(err.Error(), "out of range") {
		t.Fatalf("expected a range error, got %v", err)
	}
}

func TestParseRejectsZeroStep(t *testing.T) {
	if _, err := Parse("*/0 * * * *"); err == nil {
		t.Fatal("a zero step must fail")
	}
}

func TestEveryFifteenMinutes(t *testing.T) {
	schedule := mustParse(t, "*/15 * * * *")
	got, err := schedule.Upcoming(mustTime(t, "2024-01-01T00:07:00Z"), 4)
	if err != nil {
		t.Fatal(err)
	}
	want := []string{"00:15", "00:30", "00:45", "01:00"}
	for index, at := range got {
		if at.Format("15:04") != want[index] {
			t.Fatalf("occurrence %d = %s, want %s", index, at.Format("15:04"), want[index])
		}
	}
}

func TestWeekdayRangeSkipsTheWeekend(t *testing.T) {
	schedule := mustParse(t, "0 9 * * 1-5")
	got, err := schedule.Next(mustTime(t, "2024-01-05T10:00:00Z")) // Friday, after 09:00
	if err != nil {
		t.Fatal(err)
	}
	if got.Format(time.RFC3339) != "2024-01-08T09:00:00Z" {
		t.Fatalf("next weekday run = %s, want Monday 2024-01-08T09:00:00Z", got.Format(time.RFC3339))
	}
}

func TestSundayIsEitherZeroOrSeven(t *testing.T) {
	zero := mustParse(t, "0 0 * * 0")
	seven := mustParse(t, "0 0 * * 7")
	from := mustTime(t, "2024-01-01T00:00:30Z")
	a, err := zero.Next(from)
	if err != nil {
		t.Fatal(err)
	}
	b, err := seven.Next(from)
	if err != nil {
		t.Fatal(err)
	}
	if !a.Equal(b) || a.Weekday() != time.Sunday {
		t.Fatalf("0 and 7 must both mean Sunday: %s vs %s", a, b)
	}
}

func TestLeapDayIsFoundFourYearsOut(t *testing.T) {
	schedule := mustParse(t, "0 0 29 2 *")
	got, err := schedule.Next(mustTime(t, "2024-03-01T00:00:00Z"))
	if err != nil {
		t.Fatal(err)
	}
	if got.Format(time.RFC3339) != "2028-02-29T00:00:00Z" {
		t.Fatalf("next leap day = %s, want 2028-02-29T00:00:00Z", got.Format(time.RFC3339))
	}
}

func TestDayOfMonthAndDayOfWeekAreOred(t *testing.T) {
	schedule := mustParse(t, "0 0 1 * 1")
	// Monday the 8th matches on weekday; the 1st matches on day of month.
	got, err := schedule.Upcoming(mustTime(t, "2024-01-02T00:00:00Z"), 2)
	if err != nil {
		t.Fatal(err)
	}
	if got[0].Day() != 8 || got[1].Day() != 15 {
		t.Fatalf("Monday runs = %v, want the 8th then the 15th", got)
	}
}

func TestNeverMatchingExpressionTimesOut(t *testing.T) {
	schedule := mustParse(t, "0 0 31 2 *")
	if _, err := schedule.Next(mustTime(t, "2024-01-01T00:00:00Z")); err == nil {
		t.Fatal("31 February never matches and must report an error")
	}
}

func TestStepWithRange(t *testing.T) {
	schedule := mustParse(t, "10-40/15 * * * *")
	got, err := schedule.Upcoming(mustTime(t, "2024-01-01T00:00:00Z"), 3)
	if err != nil {
		t.Fatal(err)
	}
	want := []string{"00:10", "00:25", "00:40"}
	for index, at := range got {
		if at.Format("15:04") != want[index] {
			t.Fatalf("occurrence %d = %s, want %s", index, at.Format("15:04"), want[index])
		}
	}
}

func TestCountMustBePositive(t *testing.T) {
	schedule := mustParse(t, "* * * * *")
	if _, err := schedule.Upcoming(time.Now(), 0); err == nil {
		t.Fatal("count 0 must fail")
	}
}
