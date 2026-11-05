# {{ title }}

A text-stats service that speaks HTTP/2 with prior knowledge (`h2c`) and nothing else —
no framework, no HTTP/1 fallback, no dependencies.

```
npm start                # h2c on http://127.0.0.1:5478
npm run selftest         # 34 checks, including a real h2c round trip
npm test                 # node --test, 8 cases over a live session
bash smoke.sh            # curl --http2-prior-knowledge against every route
```

| Route | Method | Answer |
| --- | --- | --- |
| `/health` | GET | `{"status":"ok","protocol":"h2","requests":N}` |
| `/stats` | GET | `?text=…` → `{"text","lines","words","bytes"}` |
| `/stats` | POST | `{"text":"…"}` → same body |
| anything else | — | `404 {"error":"not_found","detail":"no route for GET /nope"}` |
| wrong method | — | `405 {"error":"method_not_allowed",…}` |

`missing_text`, `invalid_json` and `body_too_large` answer `422/422/413`.

## Traps this starter already paid for

1. **`http2.createServer(options, handler)` does not hand you a stream.** That second
   argument is the HTTP/1-compatible `(request, response)` pair, so a handler written as
   `(stream, headers) => …` dies with `TypeError: stream.respond is not a function`. The
   raw `Http2Stream` only arrives on the server's `stream` event, which is what this
   starter listens to.
2. **h2c needs prior knowledge.** A plain `curl` starts with HTTP/1.1 and never
   upgrades, so the body looks right while the protocol is not HTTP/2 at all. Assert
   `%{http_version}` is `2` (`curl --http2-prior-knowledge -w '%{http_version}'`), do not
   infer it from a 200.
3. **Pseudo-headers are keys.** The method is `headers[":method"]`, the target is
   `headers[":path"]` *including* the query string, and `:status` is numeric — so it has
   to be quoted inside an object literal (`{ ":status": 200 }`), not written bare.
4. **A JSON string cannot contain a literal newline.** Writing the request body as
   `'{"text":"a b\nc\n"}'` sends raw newlines, the server correctly answers
   `invalid_json`, and the failure looks like a counting bug in the wrong module. Build
   bodies with `JSON.stringify({ text: "a b\nc\n" })`.
5. **An HTTP/2 stream has no length guarantee.** Any client can stream forever, so the
   body cap has to be enforced *while reading*; once the cap is crossed the handler has
   to stop accumulating and answer `413` even though more `data` events keep arriving.
6. **Streams are concurrent by design.** Three requests in flight must not share mutable
   per-request state; the selftest and the test suite both fire three at once.
7. **`server.close()` alone never finishes** while a session is open, so a trap that only
   waits for the server hangs the step. `stop()` closes idle connections and falls back to
   `closeAllConnections()` after two seconds.
8. **`curl --http2-prior-knowledge -d …` sends no content-type.** Do not make the handler
   require `application/json`; parse the bytes and let the JSON itself decide.

## Layout

```
src/counts.js    byte-accurate wc-style counting
src/json.js      the text member scanner and the query parser
src/app.js       routing over raw Http2Stream, including 404/405/413/422 bodies
src/server.js    createServer (h2c settings) + listen + stop
src/main.js      PORT/HOST, --selftest, SIGTERM drain
src/selftest.js  checks over an in-process h2c session
tests/           node --test cases
smoke.sh         curl --http2-prior-knowledge contract
```
