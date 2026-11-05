# {{ npm_name }}

Zero-dependency sharded key-value cache. Three in-process nodes, consistent
hash ring (150 vnodes/node, FNV-1a 64a), replication to the first `--replicas`
owners. Module `{{ npm_name }}`, Go 1.24, stdlib only.

## Layout

```
go.mod        module {{ npm_name }}, go 1.24, zero deps
ring.go       consistent hash ring: Add/Remove/Owners/Points/Distribution/OwnerShifts
store.go      mutex Store, TTL on read, injectable clock
node.go       Node = name + Store
cluster.go    Cluster: Put->N owners, Get ring-order failover, Rebalance, Health
handler.go    net/http mux, pinned JSON field order
main.go       flags --addr/--replicas/--selftest, HOST/PORT, signal drain
selftest.go   35+ in-process checks, `--selftest`
chsvc_test.go 17 go tests
Makefile      build/test/selftest/smoke/clean (NAME, PORT vars)
smoke.sh      live-HTTP contract check on :5490
bin/{{ npm_name }}  wrapper: builds then exec's build/{{ npm_name }}
```

## API

| Method | Path | Result |
|---|---|---|
| GET | `/health` | `{"nodes":N,"replicas":R,"points":P,"keys":{node:count,...}}`, node keys sorted |
| PUT | `/kv/{key}` | raw value body, max 64 KiB (413 above), optional `?ttl=90s` |
| GET | `/kv/{key}` | 200 `text/plain` value, or 404 `{"error":"not_found","key":"..."}` |
| DELETE | `/kv/{key}` | 204, or 404 |
| GET | `/_ring?key=K` | `{"key":"K","owners":[...]}` ring owners |
| PUT | `/_node/{name}` | 201 added / 409 duplicate |
| DELETE | `/_node/{name}` | 200 / 404 unknown |
| * | anything else | 404 `{"error":"not_found","detail":"no route for METHOD /path"}` |
| wrong method on known path | | 405 `{"error":"method_not_allowed"}` |

Run: `make build && ./build/{{ npm_name }} --selftest && bash smoke.sh`, or
`./bin/{{ npm_name }}` (wrapper), port from `PORT` env, default 5490.

## Traps this starter already paid for

- **Raw FNV-1a is not a ring hash.** Sibling vnodes `alpha#0..alpha#149`
  differ in one trailing byte; FNV-1a's tail multiply leaves them clustered
  within ~2^33, so one node owned 1800/3000 keys (80% off even). `Hash` now
  adds an fmix64 finalizer over the FNV-1a 64a digest — still `hash/fnv`,
  still stdlib, but the 25%-even distribution test passes.
- **Map iteration order in JSON.** Go randomizes map iteration; emitting
  `keys` straight from `map[string]int` reshuffles `/health` between calls.
  The response is a pinned struct and `keys` is hand-serialized from a sorted
  name slice as `json.RawMessage` — 25 identical calls proven in tests.
- **Go's `%v` on `time.Duration`.** It prints `1m0s`, not `60000000000`;
  TTLs cross the HTTP boundary as `time.ParseDuration` strings (`?ttl=90s`),
  never `%v`-formatted numerics.
- **Ring races during rebalance.** `Rebalance` snapshots the node list and
  ring under `RLock`, then writes outside the lock; holding the write lock
  across store I/O deadlocks against `Put`'s RLock, and iterating nodes
  without the snapshot races `AddNode`. `go test -race` gates this.
- **Slice removal in `Ring.Remove`.** Building `keep/keepOwners` fresh beats
  in-place `[:0]` filtering — the in-place version aliases `owners` while
  ranging it and silently keeps stale owners on double-remove.
- **Clamping `replicas`.** `Owners(key, 9)` on 3 nodes must clamp to 3, not
  loop the ring forever emitting duplicates; without the `len(r.nodes)` cap
  the selftest spun on `o[0] != o[1]` forever.
- **413 boundary is inclusive.** 64 KiB exactly must pass, 70 KiB must not:
  read `maxValueBytes+1` and reject on `>`, not `>=` — `>=` eats the edge.
- **`set -euo pipefail` + `head`.** `cmd | head -1` kills smoke under
  pipefail when head exits early; the script uses files (`-o /dev/null`,
  `big.value`) and `|| true` instead.
