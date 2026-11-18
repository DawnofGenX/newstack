package main

import (
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strconv"
	"strings"
)

type Record struct {
	ID     string  `json:"id"`
	Email  string  `json:"email"`
	Amount float64 `json:"amount"`
}

type Summary struct {
	Count         int     `json:"count"`
	Total         float64 `json:"total"`
	UniqueEmails  int     `json:"unique_emails"`
	Invalid       int     `json:"invalid"`
	Duplicates    int     `json:"duplicates"`
}

func Process(r io.Reader) (Summary, error) {
	reader := csv.NewReader(r)
	reader.FieldsPerRecord = -1
	header, err := reader.Read()
	if err != nil {
		return Summary{}, err
	}
	if len(header) < 3 || strings.TrimSpace(header[0]) != "id" ||
		strings.TrimSpace(header[1]) != "email" ||
		strings.TrimSpace(header[2]) != "amount" {
		return Summary{}, fmt.Errorf("expected header id,email,amount")
	}

	seen := map[string]bool{}
	emails := map[string]bool{}
	var total float64
	var count int
	var invalid, duplicates int

	for {
		row, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			return Summary{}, err
		}
		if len(row) < 3 {
			invalid++
			continue
		}
		id := strings.TrimSpace(row[0])
		email := strings.TrimSpace(row[1])
		amountStr := strings.TrimSpace(row[2])
		if id == "" || email == "" || !strings.Contains(email, "@") {
			invalid++
			continue
		}
		amount, err := strconv.ParseFloat(amountStr, 64)
		if err != nil || amount < 0 {
			invalid++
			continue
		}
		if seen[id] {
			duplicates++
			continue
		}
		seen[id] = true
		emails[email] = true
		total += amount
		count++
	}

	return Summary{
		Count:        count,
		Total:        total,
		UniqueEmails: len(emails),
		Invalid:      invalid,
		Duplicates:   duplicates,
	}, nil
}

func main() {
	inPath := ""
	for i := 1; i < len(os.Args); i++ {
		if os.Args[i] == "-in" && i+1 < len(os.Args) {
			inPath = os.Args[i+1]
			i++
		}
	}
	var r io.Reader = os.Stdin
	if inPath != "" {
		f, err := os.Open(inPath)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		defer f.Close()
		r = f
	}
	summary, err := Process(r)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetEscapeHTML(false)
	if err := enc.Encode(summary); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
