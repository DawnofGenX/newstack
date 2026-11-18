package cache

import (
	"container/list"
	"time"
)

type entry[K comparable, V any] struct {
	key     K
	value   V
	expires time.Time
}

type Cache[K comparable, V any] struct {
	capacity int
	ttl      time.Duration
	items    map[K]*list.Element
	order    *list.List
	hits     int
	misses   int
}

func New[K comparable, V any](capacity int, ttl time.Duration) *Cache[K, V] {
	if capacity <= 0 {
		capacity = 1
	}
	return &Cache[K, V]{
		capacity: capacity,
		ttl:      ttl,
		items:    make(map[K]*list.Element),
		order:    list.New(),
	}
}

func (c *Cache[K, V]) now() time.Time { return time.Now() }

func (c *Cache[K, V]) Get(key K) (V, bool) {
	el, ok := c.items[key]
	if !ok {
		c.misses++
		var zero V
		return zero, false
	}
	e := el.Value.(*entry[K, V])
	if c.ttl > 0 && time.Now().After(e.expires) {
		c.order.Remove(el)
		delete(c.items, key)
		c.misses++
		var zero V
		return zero, false
	}
	c.order.MoveToFront(el)
	c.hits++
	return e.value, true
}

func (c *Cache[K, V]) Put(key K, value V) {
	if el, ok := c.items[key]; ok {
		e := el.Value.(*entry[K, V])
		e.value = value
		if c.ttl > 0 {
			e.expires = time.Now().Add(c.ttl)
		}
		c.order.MoveToFront(el)
		return
	}
	if c.order.Len() >= c.capacity {
		// evict LRU
		back := c.order.Back()
		if back != nil {
			c.order.Remove(back)
			delete(c.items, back.Value.(*entry[K, V]).key)
		}
	}
	e := &entry[K, V]{key: key, value: value}
	if c.ttl > 0 {
		e.expires = time.Now().Add(c.ttl)
	}
	el := c.order.PushFront(e)
	c.items[key] = el
}

func (c *Cache[K, V]) Len() int { return c.order.Len() }

func (c *Cache[K, V]) Stats() (hits, misses int) { return c.hits, c.misses }
