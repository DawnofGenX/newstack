package pq

import "container/heap"

type item struct {
	priority int
	seq      int
	value    string
}

type heapImpl []*item

func (h heapImpl) Len() int            { return len(h) }
func (h heapImpl) Less(i, j int) bool {
	if h[i].priority != h[j].priority {
		return h[i].priority < h[j].priority
	}
	return h[i].seq < h[j].seq
}
func (h heapImpl) Swap(i, j int) { h[i], h[j] = h[j], h[i] }
func (h *heapImpl) Push(x any)     { *h = append(*h, x.(*item)) }
func (h *heapImpl) Pop() any {
	old := *h
	n := len(old)
	x := old[n-1]
	*h = old[:n-1]
	return x
}

type PriorityQueue struct {
	h   heapImpl
	seq int
}

func New() *PriorityQueue { return &PriorityQueue{} }

func (q *PriorityQueue) Push(priority int, value string) {
	it := &item{priority: priority, seq: q.seq, value: value}
	q.seq++
	heap.Push(&q.h, it)
}

func (q *PriorityQueue) Pop() (int, string, bool) {
	if q.h.Len() == 0 {
		return 0, "", false
	}
	it := heap.Pop(&q.h).(*item)
	return it.priority, it.value, true
}

func (q *PriorityQueue) Peek() (int, string, bool) {
	if q.h.Len() == 0 {
		return 0, "", false
	}
	it := q.h[0]
	return it.priority, it.value, true
}

func (q *PriorityQueue) Len() int { return q.h.Len() }
