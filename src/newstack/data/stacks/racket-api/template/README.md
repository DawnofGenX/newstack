# Racket JSON service

A small HTTP service on Racket's bundled web server. The counting rules and the
whole route table are plain functions with no sockets in sight; only
`src/server.rkt` knows that a network exists.

## Routes

| Request | Answer |
| --- | --- |
| `GET /health` | `{"status":"ok"}` |
| `GET /stats?text=...` | `{"text":...,"lines":1,"words":2,"bytes":12}` |
| `POST /stats` with `{"text":"..."}` | the same shape, counted from the body |
| `GET`/`POST /stats` without a usable `text` | `422 {"error":"missing_text"}` |
| `POST /stats` with a body that is not a JSON object | `422 {"error":"invalid_json"}` |
| a known path with another method | `405 {"error":"method_not_allowed"}` |
| anything else | `404 {"error":"not_found","detail":"no route for GET /nope"}` |

Counting follows `wc`: a line is a `\n`, a word is a maximal run of non-space
characters, and bytes are UTF-8 bytes — `"héllo wörld\n"` is 1 line, 2 words and
**14** bytes, which is why the byte count is `bytes-length` and never
`string-length`.

## Layout

| Path | What lives there |
| --- | --- |
| `src/counts.rkt` | `count-text` and the `counts` struct |
| `src/contract.rkt` | `route`, the pure `(method, path, query, body) -> reply` function |
| `src/server.rkt` | reads the request, calls `route`, writes the reply |
| `tests/run-tests.rkt` | rackunit suite: counting table plus one case per branch |

## Run it

```sh
racket tests/run-tests.rkt
PORT=8080 racket src/server.rkt
curl 'http://127.0.0.1:8080/stats?text=hello%20world%0A'
```

`PORT` defaults to `8080` and the server listens on `127.0.0.1` only.

## Two details worth knowing

`web-server` hands the servlet a parsed `url`, not a raw request line, and its
query is already a list of decoded pairs. The server re-encodes those pairs so
`contract.rkt` stays the single place that decodes a query string — one decoder,
one set of tests.

`write-json` emits hash keys in hash order, so the JSON body's key order is not
part of the contract. Assertions compare decoded values, and the shell checks
grep for one key at a time.
