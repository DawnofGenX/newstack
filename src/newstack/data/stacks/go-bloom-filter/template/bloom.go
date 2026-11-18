package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"hash/fnv"
	"os"
)

type BloomFilter struct {
	M     uint64   `json:"m"`
	K     uint     `json:"k"`
	Bits  []uint64 `json:"bits"`
	Count uint64   `json:"count"`
}

func NewBloom(m uint64, k uint) *BloomFilter {
	words := (m + 63) / 64
	return &BloomFilter{M: m, K: k, Bits: make([]uint64, words)}
}

func fnv64a(data []byte) uint64 {
	h := fnv.New64a()
	h.Write(data)
	return h.Sum64()
}

func (bf *BloomFilter) hashes(item string) (uint64, uint64) {
	h1 := fnv64a([]byte(item))
	h2 := fnv64a(append([]byte(item), 0x9e, 0x37, 0x79, 0xb9, 0x7f, 0x4a, 0x7c, 0x15))
	if h2 == 0 {
		h2 = 1
	}
	h2 |= 1
	return h1, h2
}

func (bf *BloomFilter) Add(item string) {
	h1, h2 := bf.hashes(item)
	for i := uint(0); i < bf.K; i++ {
		idx := (h1 + uint64(i)*h2) % bf.M
		bf.Bits[idx/64] |= 1 << (idx % 64)
	}
	bf.Count++
}

func (bf *BloomFilter) Check(item string) bool {
	h1, h2 := bf.hashes(item)
	for i := uint(0); i < bf.K; i++ {
		idx := (h1 + uint64(i)*h2) % bf.M
		if bf.Bits[idx/64]&(1<<(idx%64)) == 0 {
			return false
		}
	}
	return true
}

func (bf *BloomFilter) Stats() string {
	return fmt.Sprintf("bits=%d hashes=%d added=%d", bf.M, bf.K, bf.Count)
}

func save(path string, bf *BloomFilter) error {
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	enc := json.NewEncoder(f)
	return enc.Encode(bf)
}

func load(path string) (*BloomFilter, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	var bf BloomFilter
	if err := json.NewDecoder(f).Decode(&bf); err != nil {
		return nil, err
	}
	if bf.Bits == nil {
		bf.Bits = make([]uint64, (bf.M+63)/64)
	}
	return &bf, nil
}

func main() {
	args := os.Args[1:]
	if len(args) == 0 {
		fmt.Println("usage: bloom <create|add|check|stats> ...")
		os.Exit(2)
	}
	switch args[0] {
	case "create":
		fs := flag.NewFlagSet("create", flag.ExitOnError)
		bits := fs.Uint64("bits", 1024, "number of bits")
		hashes := fs.Uint("hashes", 4, "number of hashes")
		fs.Parse(args[1:])
		if fs.NArg() < 1 {
			fmt.Println("usage: bloom create <file> [--bits N] [--hashes K]")
			os.Exit(2)
		}
		bf := NewBloom(*bits, *hashes)
		if err := save(fs.Arg(0), bf); err != nil {
			fmt.Println("error:", err)
			os.Exit(1)
		}
		fmt.Println("created")
	case "add":
		if len(args) < 3 {
			fmt.Println("usage: bloom add <file> <item>")
			os.Exit(2)
		}
		bf, err := load(args[1])
		if err != nil {
			fmt.Println("error:", err)
			os.Exit(1)
		}
		bf.Add(args[2])
		if err := save(args[1], bf); err != nil {
			fmt.Println("error:", err)
			os.Exit(1)
		}
		fmt.Println("added")
	case "check":
		if len(args) < 3 {
			fmt.Println("usage: bloom check <file> <item>")
			os.Exit(2)
		}
		bf, err := load(args[1])
		if err != nil {
			fmt.Println("error:", err)
			os.Exit(1)
		}
		if bf.Check(args[2]) {
			fmt.Println("true")
		} else {
			fmt.Println("false")
		}
	case "stats":
		if len(args) < 2 {
			fmt.Println("usage: bloom stats <file>")
			os.Exit(2)
		}
		bf, err := load(args[1])
		if err != nil {
			fmt.Println("error:", err)
			os.Exit(1)
		}
		fmt.Println(bf.Stats())
	default:
		fmt.Println("unknown command")
		os.Exit(2)
	}
}
