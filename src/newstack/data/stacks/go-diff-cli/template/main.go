package main

import (
	"bufio"
	"flag"
	"fmt"
	"os"
)

func readLines(path string) ([]string, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	var lines []string
	scanner := bufio.NewScanner(f)
	scanner.Buffer(make([]byte, 1024*1024), 1024*1024)
	for scanner.Scan() {
		lines = append(lines, scanner.Text())
	}
	return lines, scanner.Err()
}

func diffLines(old, new []string) []string {
	m, n := len(old), len(new)
	dp := make([][]int, m+1)
	for i := range dp {
		dp[i] = make([]int, n+1)
	}
	for i := m - 1; i >= 0; i-- {
		for j := n - 1; j >= 0; j-- {
			if old[i] == new[j] {
				dp[i][j] = dp[i+1][j+1] + 1
			} else if dp[i+1][j] >= dp[i][j+1] {
				dp[i][j] = dp[i+1][j]
			} else {
				dp[i][j] = dp[i][j+1]
			}
		}
	}
	var ops []string
	i, j := 0, 0
	for i < m && j < n {
		if old[i] == new[j] {
			ops = append(ops, " "+old[i])
			i++
			j++
		} else if dp[i+1][j] >= dp[i][j+1] {
			ops = append(ops, "-"+old[i])
			i++
		} else {
			ops = append(ops, "+"+new[j])
			j++
		}
	}
	for i < m {
		ops = append(ops, "-"+old[i])
		i++
	}
	for j < n {
		ops = append(ops, "+"+new[j])
		j++
	}
	return ops
}

func main() {
	oldPath := flag.String("old", "", "old file")
	newPath := flag.String("new", "", "new file")
	flag.Parse()
	args := flag.Args()
	if *oldPath == "" && len(args) >= 1 {
		*oldPath = args[0]
	}
	if *newPath == "" && len(args) >= 2 {
		*newPath = args[1]
	}
	if *oldPath == "" || *newPath == "" {
		fmt.Fprintln(os.Stderr, "usage: diff-cli -old a -new b")
		os.Exit(2)
	}
	old, err := readLines(*oldPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	newLines, err := readLines(*newPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	for _, op := range diffLines(old, newLines) {
		fmt.Println(op)
	}
	for i := range old {
		if i >= len(newLines) || old[i] != newLines[i] {
			os.Exit(1)
		}
	}
	if len(old) != len(newLines) {
		os.Exit(1)
	}
}
