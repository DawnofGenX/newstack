# {{ npm_name }}

A text-statistics service that emits W3C trace context and exports the spans it recorded.
No framework, no OpenTelemetry dependency, no vendor: the traceparent format is parsed by
hand and the spans are plain JSON.

## Layout

    trace.go          traceparent parsing, root minting, child spans
    span.go           the span record and the ring buffer that keeps recent spans
    counts.go         the text statistics (over UTF-8 bytes)
    handler.go        routes, JSON bodies, error shapes, response headers
    server.go         net/http wiring, graceful drain
    main.go           flags, --selftest, defaults
    selftest.go       the checks `--selftest` runs
    *_test.go         go test suites over a real httptest server
    smoke.sh          the same contract from the outside, with curl

## Run

    make build
    PORT=5475 ./build/{{ npm_name }}        # or ./bin/{{ npm_name }}

## Contract

| Request | Answer |
| --- | --- |
| `GET /health` | `{"status":"ok","spans":N}` |
| `GET /stats?text=…` | `{"text":"…","lines":N,"words":N,"bytes":N}` |
| `POST /stats` `{"text":"…"}` | the same body, `422 missing_text` when the member is missing or not a string |
| `GET /spans` | `{"spans":[…],"dropped":N}`, newest first; `?trace=<32 hex>` narrows it |
| anything else | `404 {"error":"not_found","detail":"no route for GET /nope"}` |
| known path, wrong method | `405 {"error":"method_not_allowed"}` |
| unparsable `traceparent` | `400 {"error":"invalid_traceparent","detail":"…"}` |
| more than 64 KiB of body | `413 {"error":"body_too_large"}` |

Every response carries `traceparent` and `x-trace-id`; a sampled `/stats` answer also carries
`x-span-id`, and its `traceparent` names the span that served the request.

## Traps this starter already paid for

1. **The response header must name the span that served the request.** The first cut set
   `traceparent` in the middleware, before any span existed, so the answer echoed the *caller's*
   span id while `x-span-id` named the request's own span — two different ids for one request and
   a child span whose parent the client never saw. The handler now overwrites the header once it
   has begun its span.
2. **W3C traceparent is stricter than it looks.** Version must be `00`, all four fields must be
   lowercase hex, and neither id may be all zeros. Uppercase hex, three fields, `ff` as a version
   and a zero trace id are all rejected here with a `400` — silently minting a new root would
   break a caller's trace without telling anyone.
3. **Sampling is a flag, not a filter.** Flags `00` still propagates the caller's ids (a response
   header is returned and children are minted), but nothing is stored. Testing this by counting
   `/spans` for one trace is the only way to be sure the flag is honoured.
4. **`json.Marshal` does not escape non-ASCII.** Go writes `héllo` as the raw bytes, so an
   expected-body literal written with `\u00e9` escapes never matches. Struct field order *is* the
   wire order (which is why every response is a struct, not a map), while map keys — the span
   attributes — are sorted by `encoding/json`.
5. **Header names canonicalise.** `x-trace-id` set by the server arrives as `X-Trace-Id`, and a
   shell check that greps for the lowercase spelling fails against a correct response. Use
   `grep -Fi` in `smoke.sh`.
6. **A ring buffer must admit what it dropped.** `/spans` keeps the last 256 spans and reports the
   evicted count instead of quietly truncating.
7. **`percentDecode` has to survive bad input.** `+` is a space, `%C3%A9` is two bytes of UTF-8,
   and a broken `%zz` stays literal — a decoder that panics or drops the `%` changes what gets
   counted.
8. **The child span's parent is the request span, not the caller's span.** Getting this backwards
   produces a flat trace that looks plausible in the export and is useless in a real tracer.

## Tests

    go vet ./... && go test ./...
    ./build/{{ npm_name }} --selftest      # 80 checks, no socket
    bash smoke.sh                    # the contract over a real socket
