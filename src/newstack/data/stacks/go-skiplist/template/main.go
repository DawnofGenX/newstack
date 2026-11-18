package main

import (
	"bufio"
	"flag"
	"fmt"
	"math/rand"
	"os"
	"strings"
)

type slNode struct {
	value string
	next  []*slNode
}

type SkipList struct {
	head  *slNode
	level int
	size  int
	rng   *rand.Rand
}

const maxLevel = 16

func NewSkipList() *SkipList {
	return &SkipList{
		head:  &slNode{next: make([]*slNode, maxLevel)},
		level: 1,
		rng:   rand.New(rand.NewSource(42)),
	}
}

func (sl *SkipList) randomLevel() int {
	lvl := 1
	for lvl < maxLevel && sl.rng.Float64() < 0.5 {
		lvl++
	}
	return lvl
}

func (sl *SkipList) Insert(v string) bool {
	update := make([]*slNode, maxLevel)
	cur := sl.head
	for i := sl.level - 1; i >= 0; i-- {
		for cur.next[i] != nil && cur.next[i].value < v {
			cur = cur.next[i]
		}
		update[i] = cur
	}
	cur = cur.next[0]
	if cur != nil && cur.value == v {
		return false
	}
	lvl := sl.randomLevel()
	if lvl > sl.level {
		for i := sl.level; i < lvl; i++ {
			update[i] = sl.head
		}
		sl.level = lvl
	}
	node := &slNode{value: v, next: make([]*slNode, lvl)}
	for i := 0; i < lvl; i++ {
		node.next[i] = update[i].next[i]
		update[i].next[i] = node
	}
	sl.size++
	return true
}

func (sl *SkipList) Contains(v string) bool {
	cur := sl.head
	for i := sl.level - 1; i >= 0; i-- {
		for cur.next[i] != nil && cur.next[i].value < v {
			cur = cur.next[i]
		}
	}
	cur = cur.next[0]
	return cur != nil && cur.value == v
}

func (sl *SkipList) Delete(v string) bool {
	update := make([]*slNode, maxLevel)
	cur := sl.head
	for i := sl.level - 1; i >= 0; i-- {
		for cur.next[i] != nil && cur.next[i].value < v {
			cur = cur.next[i]
		}
		update[i] = cur
	}
	cur = cur.next[0]
	if cur == nil || cur.value != v {
		return false
	}
	for i := 0; i < sl.level; i++ {
		if update[i].next[i] != cur {
			break
		}
		update[i].next[i] = cur.next[i]
	}
	for sl.level > 1 && sl.head.next[sl.level-1] == nil {
		sl.level--
	}
	sl.size--
	return true
}

func (sl *SkipList) Len() int { return sl.size }

func runInsert(r *bufio.Reader, sl *SkipList) error {
	scanner := bufio.NewScanner(r)
	scanner.Buffer(make([]byte, 1024*1024), 1024*1024)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}
		sl.Insert(line)
	}
	return scanner.Err()
}

func main() {
	file := flag.String("file", "", "file with values to insert (one per line)")
	contains := flag.String("contains", "", "value to look up")
	flag.Parse()

	sl := NewSkipList()
	if *file != "" && *file != "-" {
		f, err := os.Open(*file)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		defer f.Close()
		if err := runInsert(bufio.NewReader(f), sl); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	} else if *file == "-" {
		if err := runInsert(bufio.NewReader(os.Stdin), sl); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	}

	if *contains != "" {
		if sl.Contains(*contains) {
			fmt.Println("true")
		} else {
			fmt.Println("false")
		}
		return
	}
	fmt.Println(sl.Len())
}
