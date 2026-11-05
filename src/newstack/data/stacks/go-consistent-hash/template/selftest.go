package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"sort"
	"strings"
	"time"
)

type selftester struct {
	checks int
	fails  int
}

func (s *selftester) ok(cond bool, label string) {
	s.checks++
	if !cond {
		s.fails++
		fmt.Printf("  FAIL: %s\n", label)
	}
}

func eq[T comparable](s *selftester, got, want T, label string) {
	s.checks++
	if got != want {
		s.fails++
		fmt.Printf("  FAIL: %s: got %v want %v\n", label, got, want)
	}
}

// runSelftest returns process exit code: 0 clean, 1 with failures.
func runSelftest() int {
	st := &selftester{}

	// ---- ring construction ----
	ring := NewRing()
	ring.Add("alpha")
	ring.Add("beta")
	ring.Add("gamma")
	eq(st, ring.Points(), 450, "ring points after 3 adds")
	eq(st, ring.NodeCount(), 3, "node count")
	st.ok(ring.AddIfAbsent("alpha") == false, "AddIfAbsent rejects duplicate")
	eq(st, ring.Points(), 450, "points unchanged after duplicate add")

	// ownership stable under remove + re-add
	before := ring.Clone()
	ring.Remove("beta")
	ring.Add("beta")
	probe := make([]string, 500)
	for i := range probe {
		probe[i] = fmt.Sprintf("probe-%d", i)
	}
	eq(st, OwnerShifts(before, ring, probe), 0, "ownership stable under re-add")

	// distribution within 25% of even
	ring2 := NewRing()
	ring2.Add("alpha")
	ring2.Add("beta")
	ring2.Add("gamma")
	keys := make([]string, 3000)
	for i := range keys {
		keys[i] = fmt.Sprintf("key-%d", i)
	}
	dist := ring2.Distribution(keys)
	even := len(keys) / 3
	for _, n := range []string{"alpha", "beta", "gamma"} {
		d := dist[n] - even
		if d < 0 {
			d = -d
		}
		st.ok(d*100 <= even*25, fmt.Sprintf("distribution %s=%d within 25%% of %d", n, dist[n], even))
	}

	// removal moves <60% and only keys owned by the victim
	after := ring2.Clone()
	after.Remove("beta")
	shifted := OwnerShifts(ring2, after, keys)
	st.ok(shifted*100 < len(keys)*60, fmt.Sprintf("shifts %d < 60%% of %d", shifted, len(keys)))
	onlyVictim := true
	for _, k := range keys {
		if ring2.Owner(k) != after.Owner(k) && ring2.Owner(k) != "beta" {
			onlyVictim = false
			break
		}
	}
	st.ok(onlyVictim, "every moved key belonged to removed node")
	// moved count equals what beta owned (all its keys moved, none else's)
	eq(st, shifted, dist["beta"], "shifts == former owner's load")

	// wrap: synthetic key hashing above the max point maps to index 0
	// (place() wraps via modulo; verify Owners never returns empty on a full ring)
	st.ok(len(ring2.Owners("wrap-me", 2)) == 2, "wrap-around owners non-empty")

	// ---- store + injected clock ----
	base := time.Date(2026, 1, 1, 0, 0, 0, 0, time.UTC)
	now := base
	clock := func() time.Time { return now }
	store := NewStore()
	store.SetClock(clock)
	store.Put("a", "1", 0)
	store.Put("b", "2", time.Minute)
	v, ok := store.Get("a")
	st.ok(ok && v == "1", "store get no-ttl")
	v, ok = store.Get("b")
	st.ok(ok && v == "2", "store get unexpired ttl")
	eq(st, store.Len(), 2, "store len")
	eq(st, strings.Join(store.Keys(), ","), "a,b", "store keys sorted")
	now = base.Add(2 * time.Minute)
	_, ok = store.Get("b")
	st.ok(!ok, "ttl expired on read")
	eq(st, store.Len(), 1, "len after expiry")
	snap := store.Snapshot()
	st.ok(len(snap) == 1 && snap[0] == [2]string{"a", "1"}, "snapshot live entries")
	st.ok(store.Delete("a") && !store.Delete("a"), "delete true then false")

	// ---- cluster replication + rebalance ----
	now = base
	c := NewCluster([]string{"alpha", "beta", "gamma"}, 2, clock)
	owners := c.Put("session:42", "token", time.Hour)
	eq(st, len(owners), 2, "put returns 2 owners")
	st.ok(owners[0] != owners[1], "owners distinct")
	hits := 0
	for _, n := range c.Nodes {
		if _, ok := n.Get("session:42"); ok {
			hits++
		}
	}
	eq(st, hits, 2, "replica writes landed on both owners")
	v, server, ok := c.Get("session:42")
	st.ok(ok && v == "token", "cluster get value")
	st.ok(server == owners[0] || server == owners[1], "served by an owner")
	secondOwner := owners[1]
	c.RemoveNode(secondOwner)
	c.Rebalance("", owners[0])
	v, _, ok = c.Get("session:42")
	st.ok(ok && v == "token", "get survives owner removal")
	lens := c.Lens()
	eq(st, lens[secondOwner], 0, "removed node gone from lens")
	_, nodes, points := c.Health()
	eq(st, nodes, 2, "health node count after removal")
	eq(st, points, 300, "health ring points after removal")

	// Rebalance(from,to): after adding delta, keys newly owned by delta land on it
	c.AddNode("delta")
	moveKey := ""
	for i := 0; i < 5000 && moveKey == ""; i++ {
		k := fmt.Sprintf("rebalance-cand-%d", i)
		if o := c.Owners(k); len(o) > 0 && o[0] == "delta" {
			moveKey = k
		}
	}
	st.ok(moveKey != "", "found a key newly owned by delta")
	if moveKey != "" {
		c.Put(moveKey, "payload", 0)
		_, servedBy, ok := c.Get(moveKey)
		st.ok(ok && servedBy == "delta", "new node serves keys it owns post-add")
	}

	// ---- HTTP contract over a real listener ----
	httpC := NewCluster([]string{"alpha", "beta", "gamma"}, 2, nil)
	srv := httptest.NewServer(NewHandler(httpC))
	defer srv.Close()

	resp, err := http.Get(srv.URL + "/health")
	st.ok(err == nil && resp.StatusCode == 200, "GET /health 200")
	body, _ := io.ReadAll(resp.Body)
	resp.Body.Close()
	var health healthResponse
	st.ok(json.Unmarshal(body, &health) == nil, "health JSON parses")
	eq(st, health.Nodes, 3, "health nodes")
	eq(st, health.Replicas, 2, "health replicas")
	eq(st, health.Points, 450, "health points")
	st.ok(bytes.HasPrefix(bytes.TrimSpace(body), []byte(`{"nodes":3,"replicas":2,"points":450,"keys":{`)),
		"health field order pinned: "+first(string(body), 90))
	st.ok(strings.Contains(string(body), `"alpha":0`), "health keys object has alpha:0")

	putResp, err := doReq(http.MethodPut, srv.URL+"/kv/hello", "world")
	st.ok(err == nil && putResp.StatusCode == 200, "PUT /kv/hello 200")
	putResp.Body.Close()

	getResp, err := http.Get(srv.URL + "/kv/hello")
	gbody, _ := io.ReadAll(getResp.Body)
	getResp.Body.Close()
	st.ok(getResp.StatusCode == 200 && string(gbody) == "world", "GET /kv/hello returns raw value")
	st.ok(strings.HasPrefix(getResp.Header.Get("Content-Type"), "text/plain"), "GET value is text/plain")

	missResp, _ := http.Get(srv.URL + "/kv/nope")
	mbody, _ := io.ReadAll(missResp.Body)
	missResp.Body.Close()
	st.ok(missResp.StatusCode == 404 && strings.Contains(string(mbody), `"error":"not_found"`) &&
		strings.Contains(string(mbody), `"key":"nope"`), "404 body names the key")

	delResp, _ := doReq(http.MethodDelete, srv.URL+"/kv/hello", "")
	delResp.Body.Close()
	st.ok(delResp.StatusCode == 204, "DELETE -> 204")
	afterDel, _ := http.Get(srv.URL + "/kv/hello")
	afterDel.Body.Close()
	st.ok(afterDel.StatusCode == 404, "get after delete -> 404")

	// 405: POST to /health
	hreq, _ := http.NewRequest(http.MethodPost, srv.URL+"/health", nil)
	hresp, _ := http.DefaultClient.Do(hreq)
	hbody, _ := io.ReadAll(hresp.Body)
	hresp.Body.Close()
	st.ok(hresp.StatusCode == 405 && strings.Contains(string(hbody), `"error":"method_not_allowed"`), "405 body")

	// 413: 70 KiB body
	big := strings.Repeat("x", 70*1024)
	bresp, _ := doReq(http.MethodPut, srv.URL+"/kv/big", big)
	bbody, _ := io.ReadAll(bresp.Body)
	bresp.Body.Close()
	st.ok(bresp.StatusCode == 413 && strings.Contains(string(bbody), "too_large"), "413 for 70 KiB")
	edge, _ := doReq(http.MethodPut, srv.URL+"/kv/edge", strings.Repeat("y", 64*1024))
	edge.Body.Close()
	st.ok(edge.StatusCode == 200, "64 KiB exactly accepted")

	ringResp, _ := http.Get(srv.URL + "/_ring?key=abc")
	rbody, _ := io.ReadAll(ringResp.Body)
	ringResp.Body.Close()
	var ownersOut ownersResponse
	st.ok(ringResp.StatusCode == 200 && json.Unmarshal(rbody, &ownersOut) == nil &&
		len(ownersOut.Owners) == 2 && ownersOut.Key == "abc", "GET /_ring?key=abc lists owners")

	// node add/remove through the API
	dup, _ := doReq(http.MethodPut, srv.URL+"/_node/alpha", "")
	dup.Body.Close()
	st.ok(dup.StatusCode == 409, "duplicate add -> 409")
	added, _ := doReq(http.MethodPut, srv.URL+"/_node/delta", "")
	added.Body.Close()
	st.ok(added.StatusCode == 201, "add delta -> 201")
	hAfterAdd, _ := http.Get(srv.URL + "/health")
	ab, _ := io.ReadAll(hAfterAdd.Body)
	hAfterAdd.Body.Close()
	st.ok(strings.Contains(string(ab), `"points":600`) && strings.Contains(string(ab), `"nodes":4`),
		"ring grew to 600 points / 4 nodes")
	unk, _ := doReq(http.MethodDelete, srv.URL+"/_node/zeta", "")
	unk.Body.Close()
	st.ok(unk.StatusCode == 404, "unknown node delete -> 404")
	removed, _ := doReq(http.MethodDelete, srv.URL+"/_node/delta", "")
	removed.Body.Close()
	st.ok(removed.StatusCode == 200, "remove delta -> 200")
	hAfterRm, _ := http.Get(srv.URL + "/health")
	rb, _ := io.ReadAll(hAfterRm.Body)
	hAfterRm.Body.Close()
	st.ok(strings.Contains(string(rb), `"points":450`), "ring points drop back to 450")

	// key survives a node removal that does not own it
	httpC.Put("survivor", "still-here", 0)
	victim := httpC.Owners("survivor")
	if len(victim) > 0 {
		httpC.RemoveNode(victim[0])
		sv, _, ok := httpC.Get("survivor")
		st.ok(ok && sv == "still-here", "key reads after its owner is removed (replica served)")
	}

	// unknown route
	nr, _ := http.Get(srv.URL + "/nope")
	nbody, _ := io.ReadAll(nr.Body)
	nr.Body.Close()
	st.ok(nr.StatusCode == 404 && strings.Contains(string(nbody), "no route for GET /nope"), "unknown route body")

	// health JSON stability across calls (no map iteration jitter)
	stable := true
	prev := ""
	for i := 0; i < 20; i++ {
		sresp, _ := http.Get(srv.URL + "/health")
		sb, _ := io.ReadAll(sresp.Body)
		sresp.Body.Close()
		if prev != "" && string(sb) != prev {
			stable = false
		}
		prev = string(sb)
	}
	st.ok(stable, "health JSON byte-stable across 20 calls")
	names := httpC.Ring.Nodes()
	st.ok(sort.StringsAreSorted(names), "ring node names sorted")

	fmt.Printf("selftest: %d checks, %d failed\n", st.checks, st.fails)
	if st.fails > 0 {
		return 1
	}
	return 0
}

func doReq(method, url, body string) (*http.Response, error) {
	req, err := http.NewRequest(method, url, strings.NewReader(body))
	if err != nil {
		return nil, err
	}
	return http.DefaultClient.Do(req)
}

func first(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n]
}
