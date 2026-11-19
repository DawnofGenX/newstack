package main

import (
	"container/heap"
	"fmt"
	"os"
	"sort"
	"strconv"
)

// TopK returns the k largest values from nums in descending order.
func TopK(nums []float64, k int) []float64 {
	if k <= 0 {
		return []float64{}
	}
	if k >= len(nums) {
		out := append([]float64(nil), nums...)
		sort.Sort(sort.Reverse(sort.Float64Slice(out)))
		return out
	}
	// min-heap of size k
	h := &minHeap{}
	heap.Init(h)
	for _, n := range nums {
		if h.Len() < k {
			heap.Push(h, n)
		} else if n > (*h)[0] {
			heap.Pop(h)
			heap.Push(h, n)
		}
	}
	out := make([]float64, h.Len())
	for i := len(out) - 1; i >= 0; i-- {
		out[i] = heap.Pop(h).(float64)
	}
	return out
}

type minHeap []float64
func (h minHeap) Len() int            { return len(h) }
func (h minHeap) Less(i, j int) bool  { return h[i] < h[j] }
func (h minHeap) Swap(i, j int)       { h[i], h[j] = h[j], h[i] }
func (h *minHeap) Push(x interface{}) { *h = append(*h, x.(float64)) }
func (h *minHeap) Pop() interface{} {
	old := *h
	n := len(old)
	x := old[n-1]
	*h = old[:n-1]
	return x
}

func main() {
	k := 3
	var nums []float64
	args := os.Args[1:]
	i := 0
	for i < len(args) {
		if args[i] == "-k" {
			v, _ := strconv.Atoi(args[i+1])
			k = v
			i += 2
			continue
		}
		v, err := strconv.ParseFloat(args[i], 64)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(2)
		}
		nums = append(nums, v)
		i++
	}
	res := TopK(nums, k)
	for _, v := range res {
		fmt.Println(v)
	}
}