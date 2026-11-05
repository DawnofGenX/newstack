# {{ title }}

An HTTP load generator whose numbers can be trusted, plus the thresholds that turn
a load test into a gate.

```bash
{{ package_manager_install }}
{{ package_manager_run }} build
{{ package_manager_run }} stub                      # a local target on port 5471
node dist/src/main.js run --target http://127.0.0.1:5471/ok \
  --requests 200 --concurrency 8 --warmup 10 --threshold p95=250 --json report.json
```

```
target     http://127.0.0.1:5471/ok
samples    190 measured, 10 warm-up, 0 errors (0.00%)
latency    p50 0.62  p95 1.85  p99 3.10  max 4.02  mean 0.91 ms
percentile nearest-rank
throughput 4120.7 req/s over 0.046 s
threshold  p95       <= 250    ok 1.85
result     PASS
```

Exit codes: `0` every threshold held, `1` a threshold failed, `2` the run was
unusable (bad flag, unreadable file, warm-up longer than the run). With no
`--threshold` flag the run still gates `errorRate <= 0`: a load test with no
threshold is a demonstration, not a test.

## Seven things that make load-test numbers lie

1. **Coordinated omission.** If latency is measured from the moment a socket
   frees up, a server that stalls looks fast: the backlog never becomes a
   measurement. Here latency starts at `dueAt`, when the request became due, so
   queueing is inside the number.
2. **Interpolated percentiles.** Linear interpolation turns p95 of `1..100` into
   `95.05`, a latency that never happened. This uses nearest-rank and prints the
   method in every report.
3. **`Date.now()` for durations.** Wall clocks jump (NTP, suspend) and are coarse.
   Durations come from `process.hrtime.bigint()`.
4. **The mean.** One request in a hundred taking a second is invisible in a 10 ms
   mean. Gate p95 or p99; the mean is printed for orientation only.
5. **Uncounted warm-up.** The first requests pay DNS, connect, TLS and JIT. They
   are excluded from the summary and reported as `N warm-up`, so you can see what
   was dropped instead of guessing.
6. **An undrained body.** A response whose body is never read never returns its
   socket to the agent, so "keep-alive" silently opens a connection per request
   and you measure connection setup. The client drains every body.
7. **Throughput gates on shared runners.** Requests per second depend on the
   machine next to yours. Throughput is reported for humans; the CI gate is
   latency and error rate.

## Replay: gate a run you already have

`--json report.json` writes the summary *and* every sample. `replay` re-derives the
summary from that file with no network at all, which is how the arithmetic gets
tested in CI and how an archived run can be re-gated after the thresholds change.

```bash
node dist/src/main.js replay --samples samples.json --threshold p95=250
```

`--samples` takes `{"samples": [{"latencyMs": 1.2, "ok": true}]}`.

## Pointing it at something real

```bash
node dist/src/main.js run --target https://example.com/health \
  --requests 500 --concurrency 20 --warmup 20 \
  --threshold p95=300 --threshold errorRate=0.01
```

Threshold names: `p50`, `p90`, `p95`, `p99`, `max`, `mean`, `errorRate`.
