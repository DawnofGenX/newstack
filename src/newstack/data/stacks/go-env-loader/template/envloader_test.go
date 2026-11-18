package main

import (
	"reflect"
	"testing"
)

func TestParseDotEnv(t *testing.T) {
	cases := []struct {
		name string
		in   string
		want map[string]string
	}{
		{"basic", "FOO=bar\nBAZ=qux", map[string]string{"FOO": "bar", "BAZ": "qux"}},
		{"export", "export FOO=bar", map[string]string{"FOO": "bar"}},
		{"quotes", `FOO="bar baz"` + "\n" + `BAR='single'`, map[string]string{"FOO": "bar baz", "BAR": "single"}},
		{"comments", "# comment\nFOO=bar # inline", map[string]string{"FOO": "bar"}},
		{"blank", "\n\nFOO=bar\n", map[string]string{"FOO": "bar"}},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			got := ParseDotEnv(c.in)
			if !reflect.DeepEqual(got, c.want) {
				t.Fatalf("got %#v want %#v", got, c.want)
			}
		})
	}
}

func TestResolvePrecedence(t *testing.T) {
	defaults := map[string]string{"PORT": "3000", "HOST": "localhost"}
	file := map[string]string{"PORT": "4000"}
	env := map[string]string{"PORT": "5000"}
	cli := map[string]string{"PORT": "6000"}
	got := Resolve(defaults, file, env, cli)
	if got["PORT"] != "6000" {
		t.Fatalf("PORT=%s", got["PORT"])
	}
	if got["HOST"] != "localhost" {
		t.Fatalf("HOST=%s", got["HOST"])
	}
}