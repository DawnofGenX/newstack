# {{ project_name }}

{{ description }}

A JSON service written in [Standard ML](http://www.smlnj.org/sml97.html) and
compiled with [MLton](http://mlton.org/) into a single native binary. No web
framework and no JSON library: the counting rules, the JSON reader and the whole
HTTP contract are plain structures you can call from a test without opening a
socket.

```sh
make build          # compiles build/app with MLton
make test           # 40+ checks, no test framework
PORT=8080 ./bin/{{ npm_name }}
```

`HOST` (default `127.0.0.1`) and `PORT` (default `8080`) come from the
environment.

## Routes

| Method | Path | Answers |
| --- | --- | --- |
| `GET` | `/health` | `{"status":"ok"}` |
| `GET` | `/stats?text=…` | `{"text":"…","lines":1,"words":2,"bytes":12}` |
| `POST` | `/stats` | the same shape, for `{"text": "…"}` |
| `DELETE` and friends | `/health`, `/stats` | `405` `{"error":"method_not_allowed"}` |
| any | anything else | `404` `{"error":"not_found","detail":"no route for GET /nope"}` |

Missing text answers `422 {"error":"missing_text"}`. A body that is not one
well-formed JSON value answers `422 {"error":"invalid_json"}`, and a `text`
that is not a string (`{"text": 42}`) answers `missing_text`. Counting follows
`wc`: a line ends at `\n`, a word is a maximal run of non-space characters,
bytes are UTF-8 bytes (`"héllo wörld\n"` is 1 line, 2 words, 14 bytes), and the
body is counted exactly as sent.

## Layout

| Path | What it holds |
| --- | --- |
| `src/counts.sml` | the counting rules, no HTTP |
| `src/json.sml` | a strict recursive-descent JSON reader |
| `src/contract.sml` | `Route (method, path, query, body)`, the whole contract as one function |
| `src/server.sml` | SML Basis `Socket` accept loop, one request per connection |
| `src/main.sml` | `HOST`/`PORT`, then `Serve` |
| `tests/` | plain `Check()` calls; the exit code is the gate |

## Testing

```sh
make build
make test
```

## Verify

```sh
uv run newstack check sml-http-api --verbose
```
