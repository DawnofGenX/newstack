package main

import (
	"encoding/json"
	"strings"
	"testing"
)

func TestProcess(t *testing.T) {
	cases := []struct {
		name  string
		input string
		want  Summary
	}{
		{
			name:  "basic",
			input: "id,email,amount\n1,a@x.com,10.5\n2,b@x.com,20\n1,a@x.com,999\n3,c@x.com,5.25\n",
			want:  Summary{Count: 3, Total: 35.75, UniqueEmails: 3, Invalid: 0, Duplicates: 1},
		},
		{
			name:  "invalid rows",
			input: "id,email,amount\n,missing,1\n2,bademail,2\n3,c@x.com,-1\n4,d@x.com,abc\n5,e@x.com,7\n",
			want:  Summary{Count: 1, Total: 7, UniqueEmails: 1, Invalid: 4, Duplicates: 0},
		},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got, err := Process(strings.NewReader(tc.input))
			if err != nil {
				t.Fatal(err)
			}
			if got != tc.want {
				t.Fatalf("got %+v want %+v", got, tc.want)
			}
		})
	}
}

func TestGoldenOutput(t *testing.T) {
	input := "id,email,amount\n1,alice@example.com,10.50\n2,bob@example.com,20.00\n1,alice@example.com,999.00\n3,carol@example.com,5.25\n"
	got, err := Process(strings.NewReader(input))
	if err != nil {
		t.Fatal(err)
	}
	b, _ := json.Marshal(got)
	golden := `{"count":3,"total":35.75,"unique_emails":3,"invalid":0,"duplicates":1}`
	if string(b) != golden {
		t.Fatalf("got %s want %s", string(b), golden)
	}
}
