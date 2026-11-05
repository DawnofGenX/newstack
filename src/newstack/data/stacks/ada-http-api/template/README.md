# blog-count

A JSON service in Ada on GNAT.Sockets: no web framework, no JSON library — the
counting rules, the JSON reader and the whole HTTP contract are plain packages
you can call from a test without opening a socket.

```sh
make            # builds build/blog-count (gnatmake, warnings are errors)
make test       # 34 checks, no test framework
PORT=8080 ./bin/blog-count
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
well-formed JSON value answers `422 {"error":"invalid_json"}`, and a `text` that
is not a string (`{"text": 42}`) answers `missing_text` — a number is a valid
document, just not the field we asked for. Counting follows `wc`: a line ends at
`\n`, a word is a maximal run of non-space characters, bytes are UTF-8 bytes
(`"héllo wörld\n"` is 1 line, 2 words, 14 bytes), and the body is counted
exactly as sent, so `"  padded  \n"` keeps its padding.

## Layout

| Path | What it holds |
| --- | --- |
| `src/textstat-counts.ads/.adb` | the counting rules, no HTTP |
| `src/textstat-jsonbody.ads/.adb` | a validating JSON reader that keeps a number apart from a string |
| `src/textstat-contract.ads/.adb` | `Route (method, path, query, body)`, the whole contract as one function |
| `src/textstat-server.ads/.adb` | `GNAT.Sockets` accept loop, one request per connection |
| `src/app.adb` | `HOST`/`PORT`, then `Serve` |
| `tests/run_tests.adb` | plain `Check()` calls; the exit code is the gate |

## Three things worth knowing

Child units are named with a dash, not a directory: `Textstat.Server` lives in
`src/textstat-server.ads`. GNAT does not look for `src/textstat/server.ads`, and
it also needs the parent unit `src/textstat.ads` to exist before any child
compiles.

`body` is a reserved word in Ada, so the request body is a `Payload` parameter
throughout, and the reply record keeps its text in `Payload` as well.

`GNAT.Sockets` speaks `Stream_Element_Array`, not `String`: the two conversion
functions at the top of `src/textstat-server.adb` are the only place that knows
about that. Header names are matched case-insensitively, because curl sends
`Content-Length` and a plain string compare would leave the body empty.
