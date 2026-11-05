# Text stats service with Prometheus metrics

A zero-dependency Node 22+ service that counts lines, words and UTF-8 bytes, and
publishes its own Prometheus metrics. There is no framework and no `prom-client`:
the registry, the exposition format and a strict reader for that format are all in
`src/`, because the format is a contract that fails silently if you treat it as
`printf`.

## Run it

```bash
npm install            # nothing to install — this line is here so CI is identical
node src/main.js       # listens on 127.0.0.1:5474
node src/main.js --selftest   # 50 offline checks, no socket
node --test tests/*.test.js   # the same contract over a real socket
bash smoke.sh                 # the contract with curl, plus a scrape validated
```

| Route | Method | Answer |
| --- | --- | --- |
| `/health` | GET | `{"status":"ok"}` |
| `/stats` | GET | `{"text":…,"lines":N,"words":N,"bytes":N}`; `?text=` is required |
| `/stats` | POST | same, body `{"text": "…"}` (64 KiB cap) |
| `/events/:id` | GET | `{"id":"7","kind":"viewed"}`, bumps `textstat_events_seen` |
| `/metrics` | GET | Prometheus text exposition, version 0.0.4 |

Errors are machine-coded: `missing_text`, `invalid_json`, `invalid_body`,
`invalid_text`, `body_too_large` (413), `method_not_allowed` (405), `not_found`
(404 with `detail` naming the method and path).

```
src/counts.js      line/word/byte counting over raw UTF-8 bytes
src/metrics.js     the registry: counters, gauges, histograms, rendering
src/exposition.js  a strict reader for the exposition format (used by the selftest)
src/app.js         routing; every request feeds the metrics
src/server.js      node:http → fetch Request bridge
src/selftest.js    the offline contract
tools/check_scrape.mjs   validate a scrape the way Prometheus would: a pipe target
```

## Traps this starter already paid for

1. **A node `IncomingMessage` is not a fetch `Request`.** `request.url` is a bare
   path, so `new URL(request.url)` throws `TypeError: Invalid URL` and every route
   answers 500 — while an in-process test that passes a real `Request` passes. The
   bridge in `src/server.js` builds the absolute URL and streams the body
   (`duplex: "half"` is mandatory for any request with a body).
2. **`await request.text()` then a size check has already buffered the attack.**
   `readCapped()` in `src/app.js` cancels the stream the moment the cap is passed,
   and short-circuits on a declared `content-length` that is already too large.
3. **Label on the matched route pattern, never the raw path.** `/events/17` and
   `/events/18` must collapse into one series; otherwise series count follows
   traffic and the scrape grows without bound. `tests/exporter.test.js` asserts the
   collapse.
4. **Counters end in `_total`.** Not a scrape error — promlint flags it, and every
   dashboard you write against the wrong name is wrong forever. The registry
   throws at registration instead of at 3 a.m.
5. **The `+Inf` bucket must equal `_count`, and finite buckets must be cumulative.**
   Both are silent data corruption if you get them wrong: a rate computed from a
   non-monotonic bucket is nonsense. `src/exposition.js` rejects it, and
   `tools/check_scrape.mjs` applies that reader to the live payload.
6. **Label values need `\\`, `\"` and `\n` escapes.** A raw newline in a label
   splits one sample across two lines and Prometheus rejects the *whole* payload.
7. **The scrape counts itself, before it renders.** A payload rendered before the
   counter incremented always looks exactly one request behind, which reads as
   "metrics are stale" forever.
8. **`inflight_requests` is 1 inside a scrape, and that is correct.** The request
   answering the scrape is in flight while the payload is built. Asserting 0 there
   would force a lie into the exporter.
9. **Validate the body from a file, not from `$(curl …)`.** Command substitution
   strips the trailing newline, and exposition without one is invalid — so a shell
   test built on `$(…)` checks a payload no scraper ever receives.
10. **`node --test tests/` is not a directory on Node 26.** It treats `tests` as a
    file and fails `MODULE_NOT_FOUND`; use `node --test tests/*.test.js`.
11. **A histogram with a single observation still needs every bucket.** Buckets are
    emitted cumulatively whether or not anything landed in them, so a reader can
    compute a rate from any window.
