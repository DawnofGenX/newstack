package main

import (
	"bufio"
	"flag"
	"fmt"
	"hash/fnv"
	"io"
	"math"
	"os"
	"strings"
)

func mix64(x uint64) uint64 {
	x = (x ^ (x >> 30)) * 0xbf58476d1ce4e5b9
	x = (x ^ (x >> 27)) * 0x94d049bb133111b9
	return x ^ (x >> 31)
}

type HyperLogLog struct {
	p         uint8
	m         uint32
	registers []uint8
}

func NewHyperLogLog(p uint8) *HyperLogLog {
	if p < 4 {
		p = 4
	}
	if p > 16 {
		p = 16
	}
	m := uint32(1) << p
	return &HyperLogLog{p: p, m: m, registers: make([]uint8, m)}
}

func (h *HyperLogLog) Add(value string) {
	hasher := fnv.New64a()
	hasher.Write([]byte(value))
	hsh := mix64(hasher.Sum64())
	idx := uint32(hsh >> (64 - h.p))
	w := hsh << h.p
	rank := uint8(1)
	for w != 0 && (w&(1<<63)) == 0 {
		rank++
		w <<= 1
		if rank >= 64-h.p {
			break
		}
	}
	if rank > h.registers[idx] {
		h.registers[idx] = rank
	}
}

func (h *HyperLogLog) Count() float64 {
	m := float64(h.m)
	sum := 0.0
	zeros := 0
	for _, r := range h.registers {
		sum += 1.0 / math.Pow(2, float64(r))
		if r == 0 {
			zeros++
		}
	}
	if zeros == int(h.m) {
		return 0
	}
	alpha := 0.7213 / (1 + 1.079/m)
	est := alpha * m * m / sum
	if est <= 2.5*m && zeros > 0 {
		est = m * math.Log(m/float64(zeros))
	}
	return est
}

func run(in io.Reader, p uint8) (float64, error) {
	h := NewHyperLogLog(p)
	scanner := bufio.NewScanner(in)
	scanner.Buffer(make([]byte, 1024*1024), 1024*1024)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}
		h.Add(line)
	}
	if err := scanner.Err(); err != nil {
		return 0, err
	}
	return h.Count(), nil
}

func main() {
	file := flag.String("file", "", "input file (one value per line; - for stdin)")
	p := flag.Int("p", 12, "precision (4-16)")
	flag.Parse()
	var r io.Reader = os.Stdin
	if *file != "" && *file != "-" {
		f, err := os.Open(*file)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		defer f.Close()
		r = f
	}
	est, err := run(r, uint8(*p))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Printf("%.0f\n", est)
}
