// Package main implements a five-field cron expression parser and a
// next-occurrence calculator.
//
// The schedule is compiled into fixed-size lookup tables rather than compared
// field by field on every step, so advancing the clock is a handful of array
// reads. Day-of-month and day-of-week follow the classic cron rule: when both
// are restricted a day matches if either one does, and when only one is
// restricted that one decides.
package main

import (
	"fmt"
	"strconv"
	"strings"
	"time"
)

// Schedule is a parsed cron expression.
type Schedule struct {
	Spec    string
	minute  [60]bool
	hour    [24]bool
	dom     [32]bool
	month   [13]bool
	dow     [7]bool
	domStar bool
	dowStar bool
}

type fieldSpec struct {
	name  string
	low   int
	high  int
	limit int // value used when the field is "*"
}

var fields = [5]fieldSpec{
	{"minute", 0, 59, 0},
	{"hour", 0, 23, 0},
	{"day of month", 1, 31, 1},
	{"month", 1, 12, 1},
	{"day of week", 0, 7, 0}, // 7 is accepted as Sunday and folded onto 0
}

// Parse compiles a five-field cron expression.
func Parse(spec string) (*Schedule, error) {
	parts := strings.Fields(spec)
	if len(parts) != 5 {
		return nil, fmt.Errorf("expected 5 fields, got %d", len(parts))
	}
	sch := &Schedule{Spec: spec}
	tables := []func(int){
		func(v int) { sch.minute[v] = true },
		func(v int) { sch.hour[v] = true },
		func(v int) { sch.dom[v] = true },
		func(v int) { sch.month[v] = true },
		func(v int) { sch.dow[v] = true },
	}
	for index, part := range parts {
		values, err := parseField(part, fields[index])
		if err != nil {
			return nil, fmt.Errorf("%s: %w", fields[index].name, err)
		}
		for _, value := range values {
			if index == 4 && value == 7 { // Sunday may be written as 7.
				value = 0
			}
			tables[index](value)
		}
	}
	sch.domStar = strings.HasPrefix(parts[2], "*")
	sch.dowStar = strings.HasPrefix(parts[4], "*")
	return sch, nil
}

func parseField(text string, spec fieldSpec) ([]int, error) {
	var values []int
	for _, item := range strings.Split(text, ",") {
		if item == "" {
			return nil, fmt.Errorf("empty list item")
		}
		step := 1
		body := item
		if slash := strings.IndexByte(item, '/'); slash >= 0 {
			var err error
			body = item[:slash]
			step, err = strconv.Atoi(item[slash+1:])
			if err != nil || step <= 0 {
				return nil, fmt.Errorf("invalid step %q", item[slash+1:])
			}
		}
		var low, high int
		switch {
		case body == "*":
			low, high = spec.low, spec.high
		case strings.Contains(body, "-"):
			bounds := strings.SplitN(body, "-", 2)
			var err error
			if low, err = strconv.Atoi(bounds[0]); err != nil {
				return nil, fmt.Errorf("invalid value %q", bounds[0])
			}
			if high, err = strconv.Atoi(bounds[1]); err != nil {
				return nil, fmt.Errorf("invalid value %q", bounds[1])
			}
			if low > high {
				return nil, fmt.Errorf("range %s is backwards", body)
			}
		default:
			value, err := strconv.Atoi(body)
			if err != nil {
				return nil, fmt.Errorf("invalid value %q", body)
			}
			low, high = value, value
			if step > 1 {
				high = spec.high
			}
		}
		if low < spec.low || high > spec.high {
			return nil, fmt.Errorf("value out of range %d-%d: %d-%d", spec.low, spec.high, low, high)
		}
		for value := low; value <= high; value += step {
			values = append(values, value)
		}
	}
	return values, nil
}

// Matches reports whether t is exactly on the schedule.
func (s *Schedule) Matches(t time.Time) bool {
	if !s.minute[t.Minute()] || !s.hour[t.Hour()] || !s.month[int(t.Month())] {
		return false
	}
	domHit := s.dom[t.Day()]
	dowHit := s.dow[int(t.Weekday())]
	if s.domStar && s.dowStar {
		return true
	}
	if s.domStar {
		return dowHit
	}
	if s.dowStar {
		return domHit
	}
	return domHit || dowHit
}

// Next returns the first time strictly after `from` that matches the schedule.
func (s *Schedule) Next(from time.Time) (time.Time, error) {
	cursor := from.Truncate(time.Minute).Add(time.Minute)
	deadline := cursor.AddDate(5, 0, 0)
	for cursor.Before(deadline) {
		if s.Matches(cursor) {
			return cursor, nil
		}
		cursor = cursor.Add(time.Minute)
	}
	return time.Time{}, fmt.Errorf("%q never matches between %s and %s",
		s.Spec, from.Format(time.RFC3339), deadline.Format(time.RFC3339))
}

// Upcoming returns the first count matches after `from`.
func (s *Schedule) Upcoming(from time.Time, count int) ([]time.Time, error) {
	if count <= 0 {
		return nil, fmt.Errorf("count must be positive, got %d", count)
	}
	out := make([]time.Time, 0, count)
	cursor := from
	for len(out) < count {
		next, err := s.Next(cursor)
		if err != nil {
			return out, err
		}
		out = append(out, next)
		cursor = next
	}
	return out, nil
}
