package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http/httptest"
	"sort"
	"strings"
	"sync"
	"testing"
	"time"
)

func testCluster() *Cluster {
	return NewCluster([]string{"alpha", "beta", "gamma"}, 2, nil)
}

// 1
func TestRingPointsAndNodes(t *testing.T) {
	r := NewRing()
	r.Add("alpha")
	r.Add("beta")
	r.Add("gamma")
	if r.Points() != 450 {
		t.Fatalf("points = %d, want 450", r.Points())
	}
	if got := r.Nodes(); !sort.StringsAreSorted(got) || len(got) != 3 {
		t.Fatalf("nodes = %v", got)
	}
	if r.AddIfAbsent("alpha") {
		t.Fatal("re-add of existing node reported as added")
	}
	if r.Points() != 450 {
		t.Fatalf("duplicate add changed points to %d", r.Points())
	}
}

// 2
func TestRingOwnershipStableUnderReAdd(t *testing.T) {
	r := NewRing()
	r.Add("alpha")
	r.Add("beta")
	before := r.Clone()
	r.Remove("beta")
	r.Add("beta")
	keys := make([]string, 400)
	for i := range keys {
		keys[i] = fmt.Sprintf("k%d", i)
	}
	if shifts := OwnerShifts(before, r, keys); shifts != 0 {
		t.Fatalf("ownership shifted %d keys after remove+re-add", shifts)
	}
}

// 3
func TestDistributionWithin25Pct(t *testing.T) {
	r := NewRing()
	for _, n := range []string{"alpha", "beta", "gamma"} {
		r.Add(n)
	}
	keys := make([]string, 3000)
	for i := range keys {
		keys[i] = fmt.Sprintf("dk-%d", i)
	}
	dist := r.Distribution(keys)
	even := 1000
	for _, n := range []string{"alpha", "beta", "gamma"} {
		d := dist[n] - even
		if d < 0 {
			d = -d
		}
		if d*100 > even*25 {
			t.Fatalf("%s got %d keys, %d%% off even", n, dist[n], d*100/even)
		}
	}
}

// 4
func TestRemovalMovesOnlyVictimKeysUnder60Pct(t *testing.T) {
	r := NewRing()
	for _, n := range []string{"alpha", "beta", "gamma"} {
		r.Add(n)
	}
	keys := make([]string, 2000)
	for i := range keys {
		keys[i] = fmt.Sprintf("mk-%d", i)
	}
	after := r.Clone()
	after.Remove("beta")
	shifted := 0
	for _, k := range keys {
		b, a := r.Owner(k), after.Owner(k)
		if b != a {
			shifted++
			if b != "beta" {
				t.Fatalf("key %s moved but was owned by %s, not the removed node", k, b)
			}
		}
	}
	if shifted*100 >= len(keys)*60 {
		t.Fatalf("shifted %d of %d keys (>=60%%)", shifted, len(keys))
	}
	if shifted == 0 {
		t.Fatal("removing beta moved no keys")
	}
}

// 5
func TestOwnersClockwiseWrapAndDistinct(t *testing.T) {
	r := NewRing()
	for _, n := range []string{"alpha", "beta", "gamma"} {
		r.Add(n)
	}
	for i := 0; i < 300; i++ {
		k := fmt.Sprintf("owrap-%d", i)
		o := r.Owners(k, 2)
		if len(o) != 2 || o[0] == o[1] {
			t.Fatalf("owners for %s = %v", k, o)
		}
		// primary must equal first point >= hash or wrap to index 0
		idx := r.Placement(k)
		if idx < 0 || idx >= r.Points() {
			t.Fatal("placement out of range")
		}
	}
	// replicas beyond node count clamps
	if o := r.Owners("x", 9); len(o) != 3 {
		t.Fatalf("clamp: owners = %v", o)
	}
}

// 6
func TestStoreTTLAndInjectedClock(t *testing.T) {
	base := time.Date(2026, 3, 1, 12, 0, 0, 0, time.UTC)
	now := base
	s := NewStore()
	s.SetClock(func() time.Time { return now })
	s.Put("k", "v", 30*time.Second)
	if v, ok := s.Get("k"); !ok || v != "v" {
		t.Fatal("fresh TTL key missing")
	}
	now = base.Add(31 * time.Second)
	if _, ok := s.Get("k"); ok {
		t.Fatal("expired key still readable")
	}
	if s.Len() != 0 {
		t.Fatalf("Len = %d after expiry", s.Len())
	}
	s.Put("n", "1", 0)
	if _, ok := s.Get("n"); !ok {
		t.Fatal("no-TTL key expired")
	}
}

// 7
func TestStoreKeysSnapshotLen(t *testing.T) {
	s := NewStore()
	s.Put("b", "2", 0)
	s.Put("a", "1", 0)
	s.Put("c", "3", 0)
	if got := strings.Join(s.Keys(), ","); got != "a,b,c" {
		t.Fatalf("Keys = %s", got)
	}
	snap := s.Snapshot()
	if len(snap) != 3 || snap[0] != [2]string{"a", "1"} || snap[2] != [2]string{"c", "3"} {
		t.Fatalf("Snapshot = %v", snap)
	}
	if s.Len() != 3 {
		t.Fatalf("Len = %d", s.Len())
	}
	if !s.Delete("b") || s.Delete("b") {
		t.Fatal("Delete semantics wrong")
	}
	if s.Len() != 2 {
		t.Fatalf("Len = %d after delete", s.Len())
	}
}

// 8
func TestNodeDelegatesToStore(t *testing.T) {
	n := NewNode("alpha")
	n.Put("x", "1", 0)
	if v, ok := n.Get("x"); !ok || v != "1" {
		t.Fatal("node get failed")
	}
	if n.Len() != 1 {
		t.Fatal("node len")
	}
	if !n.Delete("x") || n.Len() != 0 {
		t.Fatal("node delete")
	}
}

// 9
func TestClusterPutWritesToFirstTwoOwners(t *testing.T) {
	c := testCluster()
	owners := c.Put("user:1", "carol", time.Minute)
	if len(owners) != 2 || owners[0] == owners[1] {
		t.Fatalf("owners = %v", owners)
	}
	hits := 0
	for _, n := range c.Nodes {
		if _, ok := n.Get("user:1"); ok {
			hits++
		}
	}
	if hits != 2 {
		t.Fatalf("replicated to %d nodes, want 2", hits)
	}
}

// 10
func TestClusterGetTriesOwnersInRingOrder(t *testing.T) {
	c := testCluster()
	owners := c.Put("order:key", "v", 0)
	v, served, ok := c.Get("order:key")
	if !ok || v != "v" {
		t.Fatal("get failed")
	}
	if served != owners[0] {
		t.Fatalf("served by %s, want primary %s", served, owners[0])
	}
	// wipe primary; second owner must still serve
	for _, n := range c.Nodes {
		if n.Name == owners[0] {
			n.Delete("order:key")
		}
	}
	_, served, ok = c.Get("order:key")
	if !ok || served != owners[1] {
		t.Fatalf("fallback served by %s ok=%v, want %s", served, ok, owners[1])
	}
}

// 11
func TestClusterGetSurvivesOwnerRemoval(t *testing.T) {
	c := testCluster()
	owners := c.Put("keep:me", "payload", 0)
	c.RemoveNode(owners[0])
	v, served, ok := c.Get("keep:me")
	if !ok || v != "payload" {
		t.Fatalf("get after owner removal: %q ok=%v", v, ok)
	}
	if served == owners[0] {
		t.Fatal("served by removed node")
	}
	if _, nodes, _ := c.Health(); nodes != 2 {
		t.Fatalf("nodes = %d", nodes)
	}
}

// 12
func TestClusterRebalanceAfterAdd(t *testing.T) {
	c := testCluster()
	c.AddNode("delta")
	moveKey := ""
	for i := 0; i < 10000 && moveKey == ""; i++ {
		k := fmt.Sprintf("rb-%d", i)
		if o := c.Owners(k); len(o) > 0 && o[0] == "delta" {
			moveKey = k
		}
	}
	if moveKey == "" {
		t.Fatal("no key became delta-owned after add")
	}
	c.Put(moveKey, "v", 0)
	_, served, ok := c.Get(moveKey)
	if !ok || served != "delta" {
		t.Fatalf("%s served by %s, want delta", moveKey, served)
	}
	// Rebalance is idempotent and non-destructive here
	c.Rebalance("alpha", "delta")
	if v, _, ok := c.Get(moveKey); !ok || v != "v" {
		t.Fatal("key lost during rebalance")
	}
}

// 13
func TestHealthSortedStableJSON(t *testing.T) {
	c := testCluster()
	c.Put("k1", "v", 0)
	h := NewHandler(c)
	var prev string
	for i := 0; i < 25; i++ {
		rec := httptest.NewRecorder()
		h.ServeHTTP(rec, httptest.NewRequest("GET", "/health", nil))
		body := rec.Body.String()
		if prev != "" && body != prev {
			t.Fatalf("health JSON unstable:\n%s\n%s", prev, body)
		}
		prev = body
	}
	if !strings.HasPrefix(prev, `{"nodes":3,"replicas":2,"points":450,"keys":{"alpha":`) {
		t.Fatalf("health shape wrong: %s", prev)
	}
	var m map[string]any
	if err := json.Unmarshal([]byte(prev), &m); err != nil {
		t.Fatalf("health not valid JSON: %v", err)
	}
}

// 14
func TestHandlerKVPutGetDelete(t *testing.T) {
	h := NewHandler(testCluster())
	do := func(method, path, body string) (int, string, string) {
		rec := httptest.NewRecorder()
		req := httptest.NewRequest(method, path, strings.NewReader(body))
		h.ServeHTTP(rec, req)
		b, _ := io.ReadAll(rec.Body)
		return rec.Code, string(b), rec.Header().Get("Content-Type")
	}
	code, _, _ := do("PUT", "/kv/greeting", "hi")
	if code != 200 {
		t.Fatalf("put code %d", code)
	}
	code, body, ct := do("GET", "/kv/greeting", "")
	if code != 200 || body != "hi" || !strings.HasPrefix(ct, "text/plain") {
		t.Fatalf("get: %d %q %s", code, body, ct)
	}
	code, _, _ = do("DELETE", "/kv/greeting", "")
	if code != 204 {
		t.Fatalf("delete code %d", code)
	}
	code, body, _ = do("GET", "/kv/greeting", "")
	if code != 404 || !strings.Contains(body, `"error":"not_found"`) || !strings.Contains(body, `"key":"greeting"`) {
		t.Fatalf("miss: %d %s", code, body)
	}
}

// 15
func TestHandlerSizeLimitsAndErrors(t *testing.T) {
	h := NewHandler(testCluster())
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest("PUT", "/kv/big", strings.NewReader(strings.Repeat("z", 70*1024))))
	if rec.Code != 413 || !strings.Contains(rec.Body.String(), "too_large") {
		t.Fatalf("70KiB: %d %s", rec.Code, rec.Body.String())
	}
	rec = httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest("PUT", "/kv/edge", strings.NewReader(strings.Repeat("z", 64*1024))))
	if rec.Code != 200 {
		t.Fatalf("64KiB edge: %d", rec.Code)
	}
	rec = httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest("POST", "/health", nil))
	if rec.Code != 405 || !strings.Contains(rec.Body.String(), `"error":"method_not_allowed"`) {
		t.Fatalf("405: %d %s", rec.Code, rec.Body.String())
	}
	rec = httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest("GET", "/bogus", nil))
	if rec.Code != 404 || !strings.Contains(rec.Body.String(), "no route for GET /bogus") {
		t.Fatalf("404 route: %d %s", rec.Code, rec.Body.String())
	}
}

// 16
func TestHandlerNodeLifecycle(t *testing.T) {
	h := NewHandler(testCluster())
	do := func(method, path string) int {
		rec := httptest.NewRecorder()
		h.ServeHTTP(rec, httptest.NewRequest(method, path, nil))
		return rec.Code
	}
	if c := do("PUT", "/_node/alpha"); c != 409 {
		t.Fatalf("dup add code %d", c)
	}
	if c := do("PUT", "/_node/delta"); c != 201 {
		t.Fatalf("add code %d", c)
	}
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest("GET", "/health", nil))
	if !strings.Contains(rec.Body.String(), `"points":600`) {
		t.Fatalf("after add: %s", rec.Body.String())
	}
	if c := do("DELETE", "/_node/zeta"); c != 404 {
		t.Fatalf("unknown delete code %d", c)
	}
	if c := do("DELETE", "/_node/delta"); c != 200 {
		t.Fatalf("delete code %d", c)
	}
	rec = httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest("GET", "/health", nil))
	if !strings.Contains(rec.Body.String(), `"points":450`) {
		t.Fatalf("after remove: %s", rec.Body.String())
	}
	rec = httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest("GET", "/_ring?key=abc", nil))
	if rec.Code != 200 {
		t.Fatalf("ring code %d", rec.Code)
	}
	var o ownersResponse
	if err := json.Unmarshal(rec.Body.Bytes(), &o); err != nil || o.Key != "abc" || len(o.Owners) != 2 {
		t.Fatalf("ring body %s err %v", rec.Body.String(), err)
	}
}

// 17
func TestConcurrentReadWriteRebalance(t *testing.T) {
	c := testCluster()
	var wg sync.WaitGroup
	for w := 0; w < 8; w++ {
		wg.Add(2)
		go func(w int) {
			defer wg.Done()
			for i := 0; i < 100; i++ {
				c.Put(fmt.Sprintf("cc-%d-%d", w, i), "v", 0)
			}
		}(w)
		go func(w int) {
			defer wg.Done()
			for i := 0; i < 100; i++ {
				c.Get(fmt.Sprintf("cc-%d-%d", w, i))
				c.Owners(fmt.Sprintf("cc-%d-%d", w, i))
			}
		}(w)
	}
	wg.Add(1)
	go func() {
		defer wg.Done()
		c.AddNode("delta")
		c.Rebalance("alpha", "delta")
		c.RemoveNode("delta")
	}()
	wg.Wait()
	c.Put("final", "v", 0)
	if v, _, ok := c.Get("final"); !ok || v != "v" {
		t.Fatal("cluster broken after concurrency")
	}
}
