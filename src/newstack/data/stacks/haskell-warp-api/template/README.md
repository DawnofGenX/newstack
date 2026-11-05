# {{ title }}

{{ description }}

A Warp JSON service in Haskell that counts lines, words and bytes the way `wc`
does. `Counts` holds the counting rule and the tiny JSON writer, `Contract` is
one pure function from (method, path, query, body) to (status, body) so every
status code is testable without a socket, and `app/Main.hs` is the only place
that touches WAI.

## Endpoints

| Method | Path | Answer |
| --- | --- | --- |
| `GET` | `/health` | `200 {"status":"ok"}` |
| `GET` | `/stats?text=...` | `200 {"text","lines","words","bytes"}`, `422 {"error":"missing_text"}` when `text` is absent |
| `POST` | `/stats` with `{"text": "..."}` | same body as `GET`; `422 {"error":"missing_text"}` for a non-string `text`, `422 {"error":"invalid_json"}` for a body that is not one JSON object |
| any | a known path with another method | `405 {"error":"method_not_allowed"}` |
| any | anything else | `404 {"error":"not_found","detail":"no route for METHOD /path"}` |

The text is counted exactly as sent: `"  padded  \\n"` is one line, one word and
eleven bytes, and a trailing newline is a line of its own.

## Why a hand-written JSON reader

The service needs exactly one thing from JSON: read the `text` field of a posted
object and tell a string from everything else. `aeson` would drag a large
dependency tree in for that, so `Contract.parseText` is a small parser that
handles objects, arrays, strings (with `\\uXXXX` escapes), numbers, booleans and
null, and answers `Left ()` for anything malformed. `Counts.quoteJson` writes the
responses, which only ever contain strings and integers.

Warp hands the query string over with its leading `?` still attached, so
`Contract.dropQuestion` strips it before the parameters are split.

## Running it

```sh
cabal build all
cabal test all
PORT=8080 "$(cabal list-bin exe:{{ npm_name }})"
curl 'http://127.0.0.1:8080/stats?text=hello%20world%0A'
```

The first `cabal build` compiles Warp and its dependencies and takes a few
minutes; after that the store is warm and rebuilds are seconds.

## Layout

```
{{ cabal_name }}.cabal          the library, the executable and the test suite
src/Counts.hs                  the counting rule and the response writer
src/Contract.hs                pure routing: status codes, JSON bodies, the body parser
app/Main.hs                    WAI glue: read the request, ask Contract, answer
test/Spec.hs                   an exitcode-stdio suite, no test framework dependency
```
