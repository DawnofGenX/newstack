# Prolog HTTP service

A JSON service on SWI-Prolog's own web server. The route table is a single
predicate that takes `(Method, Path, Query, Body)` and returns
`reply(Status, Dict)` — no socket, no request object, so the tests call it
directly.

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
characters, and bytes are UTF-8 bytes. Prolog works in code points, so the byte
count adds each character's UTF-8 width — `"héllo wörld\n"` is 1 line, 2 words
and **14** bytes.

## Layout

| Path | What lives there |
| --- | --- |
| `src/counts.pl` | `count_text/2`: the counting rules |
| `src/contract.pl` | `route/5`: the whole route table as one pure predicate |
| `src/server.pl` | reads the request, calls the contract, writes the reply |
| `tests/run-tests.pl` | 21 checks: the counting table plus one case per branch |

## Run it

```sh
swipl -q tests/run-tests.pl
PORT=8080 swipl -q src/server.pl
curl 'http://127.0.0.1:8080/stats?text=hello%20world%0A'
```

`PORT` defaults to `8080` and the socket is bound to `127.0.0.1`.

## Three details worth knowing

SWI parses the query string for you: a request carries `search(Pairs)` with the
pairs already decoded as atoms. The server re-encodes them with
`uri_query_components/2` so `contract.pl` stays the only decoder, and its tests
cover the decoding.

The request stream ends where `Content-Length` says it does, not at end of file,
so the body is read for exactly that many characters — a `GET` with no body then
reads nothing instead of blocking until the client gives up.

`library(http/json)` keeps JSON strings as Prolog strings and numbers as
numbers, which is what lets `{"text": 42}` be a `422` while `{"text": "42"}`
counts one word.
