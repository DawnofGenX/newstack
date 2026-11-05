# blog-count

A small JSON service written in Haxe, run on the eval target: no build step,
no haxelib, no compiled output to clean up.

```sh
haxe --interp -cp src -cp tests --main TextstatTests   # 57 checks, no framework
PORT=8080 ./bin/blog-count                             # serve on 127.0.0.1:8080
```

`bin/blog-count` is a two-line wrapper around `haxe --interp -cp src --main
textstat.App`, so it honours `HOST` (default `127.0.0.1`) and `PORT` (default
`8080`).

## Routes

| Method | Path | Answers |
| --- | --- | --- |
| `GET` | `/health` | `{"status":"ok"}` |
| `GET` | `/stats?text=…` | `{"text":"…","lines":1,"words":2,"bytes":12}` |
| `POST` | `/stats` | the same shape, for `{"text": "…"}` |
| any | `/health`, `/stats` | `405` `{"error":"method_not_allowed"}` |
| any | anything else | `404` `{"error":"not_found","detail":"no route for GET /nope"}` |

Missing text answers `422 {"error":"missing_text"}`; a body that is not JSON, or
a `text` that is not a string (`{"text": 42}`), also answers `422` — the first
as `invalid_json`, the second as `missing_text`. Counting follows `wc`: a line
ends at `\n`, a word is a maximal run of non-space characters, and bytes are
UTF-8 bytes (`"héllo wörld\n"` is 1 line, 2 words, 14 bytes). The body is
counted exactly as sent, so `"  padded  \n"` keeps its padding.

## Layout

| Path | What it holds |
| --- | --- |
| `src/textstat/Counts.hx` | the counting rules, no HTTP |
| `src/textstat/TextKind.hx` | what a request body turned out to be |
| `src/textstat/JsonBody.hx` | a JSON reader that keeps a number apart from a string |
| `src/textstat/Contract.hx` | `route(method, path, query, body)`, the whole contract as one pure function |
| `src/textstat/Server.hx` | one request per connection on `sys.net.Socket` |
| `src/textstat/App.hx` | `HOST`/`PORT`, then the accept loop |
| `tests/TextstatTests.hx` | plain `check()` calls; the exit code is the gate |

## Two things worth knowing

`sys.net.Socket` on the eval target has no `setOption`, so there is no way to
ask for `SO_REUSEADDR`. Instead of closing first and parking the listening port
in `TIME_WAIT` for a minute (the next start would die with
`Unix.Unix_error(Unix.EADDRINUSE, "bind", "")` while the port looks free),
the server drains the connection until the client hangs up and only then
closes its own side, so the `TIME_WAIT` lands on the client's ephemeral port.

The JSON reader is hand-written for the same reason the counters are: it has to
say "this is valid JSON but there is no string `text`" (`422 missing_text`)
apart from "this is not JSON" (`422 invalid_json`), decode `\u00e9` and
`\ud83d\ude42` into real UTF-8 bytes, and reject trailing rubbish after the
object.
