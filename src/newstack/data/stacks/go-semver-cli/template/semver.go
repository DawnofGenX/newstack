package main

import (
	"fmt"
	"strconv"
	"strings"
)

// Version is a semantic version with optional prerelease identifiers.
type Version struct {
	Major int
	Minor int
	Patch int
	Pre   []string
}

// Parse reads a semantic version such as 1.4.2-rc.1+build.7.
func Parse(raw string) (Version, error) {
	text := strings.TrimSpace(raw)
	if text == "" {
		return Version{}, fmt.Errorf("empty version")
	}
	if i := strings.IndexByte(text, '+'); i >= 0 {
		text = text[:i]
	}
	var pre []string
	if i := strings.IndexByte(text, '-'); i >= 0 {
		pre = strings.Split(text[i+1:], ".")
		text = text[:i]
		for _, part := range pre {
			if part == "" {
				return Version{}, fmt.Errorf("invalid prerelease in %q", raw)
			}
		}
	}
	parts := strings.Split(text, ".")
	if len(parts) != 3 {
		return Version{}, fmt.Errorf("version must have major.minor.patch: %q", raw)
	}
	nums := make([]int, 3)
	for i, part := range parts {
		if part == "" {
			return Version{}, fmt.Errorf("empty component in %q", raw)
		}
		n, err := strconv.Atoi(part)
		if err != nil {
			return Version{}, fmt.Errorf("non numeric component in %q", raw)
		}
		if n < 0 {
			return Version{}, fmt.Errorf("negative component in %q", raw)
		}
		nums[i] = n
	}
	return Version{Major: nums[0], Minor: nums[1], Patch: nums[2], Pre: pre}, nil
}

func (v Version) String() string {
	out := fmt.Sprintf("%d.%d.%d", v.Major, v.Minor, v.Patch)
	if len(v.Pre) > 0 {
		out += "-" + strings.Join(v.Pre, ".")
	}
	return out
}

func comparePre(a, b []string) int {
	if len(a) == 0 && len(b) == 0 {
		return 0
	}
	if len(a) == 0 {
		return 1
	}
	if len(b) == 0 {
		return -1
	}
	for i := 0; i < len(a) && i < len(b); i++ {
		ai, aerr := strconv.Atoi(a[i])
		bi, berr := strconv.Atoi(b[i])
		switch {
		case aerr == nil && berr == nil:
			if ai != bi {
				return sign(ai - bi)
			}
		case aerr == nil:
			return -1
		case berr == nil:
			return 1
		default:
			if a[i] != b[i] {
				if a[i] < b[i] {
					return -1
				}
				return 1
			}
		}
	}
	return sign(len(a) - len(b))
}

func sign(n int) int {
	switch {
	case n < 0:
		return -1
	case n > 0:
		return 1
	default:
		return 0
	}
}

// Compare returns -1, 0 or 1 for a<b, a==b, a>b.
func Compare(a, b Version) int {
	if d := sign(a.Major - b.Major); d != 0 {
		return d
	}
	if d := sign(a.Minor - b.Minor); d != 0 {
		return d
	}
	if d := sign(a.Patch - b.Patch); d != 0 {
		return d
	}
	return comparePre(a.Pre, b.Pre)
}

func parseRangePart(part string) (int, Version, error) {
	fields := strings.Split(part, ".")
	components := len(fields)
	for i, field := range fields {
		if strings.ContainsAny(field, "*xX") {
			components = i
			break
		}
	}
	if components == 0 {
		return 0, Version{}, fmt.Errorf("constraint %q has no version component", part)
	}
	padded := append([]string{}, fields[:components]...)
	for len(padded) < 3 {
		padded = append(padded, "0")
	}
	v, err := Parse(strings.Join(padded, "."))
	return components, v, err
}

// Satisfies reports whether v matches a single constraint expression.
func Satisfies(v Version, constraint string) (bool, error) {
	expr := strings.TrimSpace(constraint)
	if expr == "" {
		return false, fmt.Errorf("empty constraint")
	}
	if expr == "*" {
		return true, nil
	}
	for _, prefix := range []string{">=", "<=", "^", "~", ">", "<", "="} {
		if !strings.HasPrefix(expr, prefix) {
			continue
		}
		body := strings.TrimSpace(strings.TrimPrefix(expr, prefix))
		components, target, err := parseRangePart(body)
		if err != nil {
			return false, err
		}
		switch prefix {
		case ">=":
			return Compare(v, target) >= 0, nil
		case "<=":
			return Compare(v, target) <= 0, nil
		case ">":
			return Compare(v, target) > 0, nil
		case "<":
			return Compare(v, target) < 0, nil
		case "=":
			return Compare(v, target) == 0, nil
		case "^":
			if Compare(v, target) < 0 {
				return false, nil
			}
			return Compare(v, caretUpper(target)) < 0, nil
		case "~":
			if Compare(v, target) < 0 {
				return false, nil
			}
			return Compare(v, tildeUpper(target, components)) < 0, nil
		}
	}
	components, target, err := parseRangePart(expr)
	if err != nil {
		return false, err
	}
	switch components {
	case 1:
		return target.Major == v.Major, nil
	case 2:
		return target.Major == v.Major && target.Minor == v.Minor, nil
	default:
		return Compare(v, target) == 0, nil
	}
}

func caretUpper(v Version) Version {
	switch {
	case v.Major > 0:
		return Version{Major: v.Major + 1}
	case v.Minor > 0:
		return Version{Major: 0, Minor: v.Minor + 1}
	default:
		return Version{Major: 0, Minor: 0, Patch: v.Patch + 1}
	}
}

func tildeUpper(v Version, components int) Version {
	if components < 2 {
		return Version{Major: v.Major + 1}
	}
	return Version{Major: v.Major, Minor: v.Minor + 1}
}
