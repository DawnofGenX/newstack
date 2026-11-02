package app

import (
	"bytes"
	"strings"
	"testing"
)

func TestRun(t *testing.T) {
	tests := []struct {
		name       string
		args       []string
		wantCode   int
		wantOut    string
		wantErrSub string
	}{
		{
			name:     "greet default",
			args:     []string{"greet"},
			wantCode: 0,
			wantOut:  "Hello, world!\n",
		},
		{
			name:     "greet named",
			args:     []string{"greet", "--name", "you"},
			wantCode: 0,
			wantOut:  "Hello, you!\n",
		},
		{
			name:     "version",
			args:     []string{"--version"},
			wantCode: 0,
			wantOut:  Version + "\n",
		},
		{
			name:       "unknown flag",
			args:       []string{"greet", "--nope"},
			wantCode:   2,
			wantErrSub: "flag provided but not defined",
		},
		{
			name:       "unknown command",
			args:       []string{"bogus"},
			wantCode:   2,
			wantErrSub: "unknown command",
		},
		{
			name:       "no arguments",
			args:       nil,
			wantCode:   2,
			wantErrSub: "Usage:",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var stdout, stderr bytes.Buffer

			got := Run(tt.args, &stdout, &stderr)

			if got != tt.wantCode {
				t.Fatalf("exit code = %d, want %d (stderr: %q)", got, tt.wantCode, stderr.String())
			}
			if stdout.String() != tt.wantOut {
				t.Errorf("stdout = %q, want %q", stdout.String(), tt.wantOut)
			}
			if tt.wantErrSub != "" && !strings.Contains(stderr.String(), tt.wantErrSub) {
				t.Errorf("stderr = %q, want it to contain %q", stderr.String(), tt.wantErrSub)
			}
		})
	}
}
