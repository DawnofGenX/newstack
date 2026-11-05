# {{ title }}

An HTTP cache is a bet about the future: *this body will still be good in sixty seconds*. This stack implements the
other half of the bet — the conditional request that settles it — and measures what the bet saves.

Everything here is RFC 9110 behaviour you can watch: a real `node:http` server, a real client, and a demo whose six
stories fail loudly if a rule is broken.

## The rules this node keeps

1. **A tag identifies a representation, not a document.** The ETag is the first 16 hex characters of a SHA-256 over the
   bytes actually sent, so two representations of one URL have different tags.
2. **`If-None-Match` compares weakly, `If-Match` compares strongly.** The weak comparison ignores the `W/` prefix, so a
   weak tag answers `304 Not Modified`. The strong comparison does not, so `If-Match: W/"x"` answers `412 Precondition
   Failed` — and so does `If-Match: W/"x"` when the current tag is also `W/"x"`. A weak tag can say "unchanged"; it can
   never authorise a write.
3. **`If-None-Match` outranks `If-Modified-Since`.** A date has one-second resolution and can only say "maybe older". If
   both headers arrive, the tag decides; a cache that reads the date first refetches a body it already holds.
4. **A `304` carries no body, and that is the whole point.** The status is the saving: zero bytes on the wire instead of
   the full representation. The response still carries the ETag and `Cache-Control`, because the cache needs both.
5. **A `304` refreshes the stored entry; it does not replace it.** A cache that assigns the empty 304 body to its entry
   erases the document and keeps serving the emptiness for the rest of the fresh window. Nothing throws — that is why
   the demo runs the mistake on purpose and reads the entry afterwards.
6. **`Vary: accept` means the URL is not the key.** One URL, two representations, and a cache keyed by URL alone hands
   JSON to a client that asked for text.
7. **`no-store` is not a lifetime of zero.** It is an instruction not to store the response at all.

## Run the demo

```
$ npm run build && node dist/src/main.js demo
1. a 304 carries no body
  first request   200, 59 byte(s), "ba6c37b42f121c2c"
  conditional     304, 0 byte(s) of body
  the tag is the same document, so the body was not sent twice
  saved           59 byte(s)
  kept        yes

2. If-None-Match compares weakly, If-Match strongly
  If-None-Match: W/"ba6c37b42f121c2c"   -> 304 (weak comparison ignores W/)
  If-Match:      W/"ba6c37b42f121c2c"   -> 412 (strong comparison only)
  If-Match:      "ba6c37b42f121c2c" -> 204
  so a weak tag can say "unchanged" but can never authorise a write
  kept        yes

3. If-None-Match wins over If-Modified-Since
  date alone                    -> 200 (the stored copy looks old)
  date and a matching tag       -> 304 (the tag is more precise)
  a cache that reads the date first refetches a body it already has
  kept        yes

4. Vary: accept means the URL alone is not a key
  json keyed by url   { "total": 3, "note": "json for ma
  text keyed by url   { "total": 3, "note": "json for ma   <- wrong representation
  json keyed by vary  { "total": 3, "note": "json for ma
  text keyed by vary  /report v1
  kept        yes

5. a 304 refreshes freshness, it does not empty the body
  stored          17 byte(s)
  after a 304     17 byte(s), revalidated true
  next hit        17 byte(s)
  drop-on-304     17 -> 0 byte(s), lost true
  its next hit    0 byte(s): the entry is now empty and still fresh
  kept        yes

6. the saved bytes are counted, not estimated
  20 rounds       17 byte(s) over the wire
  always 200      340 byte(s)
  hits            15
  revalidations   4
  saved           323 byte(s) (95.0%)
  ttl parsed      1000 ms from max-age=1
  kept        yes
```

## Use it

```ts
import { HttpCache } from "./cache.js";

const cache = new HttpCache("http://127.0.0.1:5479");
await cache.get("/profile");           // 200, stored with its ETag and max-age
await cache.get("/profile");           // fresh: served from memory, zero bytes
// later, once the window closes: revalidated with If-None-Match, 304, body kept
```

Serve the demo documents to look at the headers yourself:

```
node dist/src/main.js serve --port 5479
curl -i http://127.0.0.1:5479/profile
curl -i -H 'If-None-Match: "<the tag>"' http://127.0.0.1:5479/profile
```

## Exit codes

| code | meaning |
| --- | --- |
| 0 | every story kept, or the command succeeded |
| 1 | a story broke its rule, or a measured contract was not met |
| 2 | the command line could not be understood |

## Layout

```
src/etag.ts       parse, render, compare tags; the weak and strong rules
src/resource.ts   documents, representations, Cache-Control
src/server.ts     the HTTP server and the decision order
src/cache.ts      a client cache: freshness, revalidation, Vary keys
src/cli.ts        demo | check | serve | selftest
src/selftest.ts   the rules above, checked
```

## What this stack does not do

It does not implement a proxy cache, `stale-while-revalidate`, `must-revalidate`, or range requests, and it does not
pretend a single-process in-memory cache is a CDN. The point is the conditional-request protocol, which every one of
those builds on.
