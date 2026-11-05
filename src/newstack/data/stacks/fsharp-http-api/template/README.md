# {{ title }}

{{ description }}

An F# 8 / .NET 8 JSON service with no web framework: `Server.fs` accepts a
`TcpListener` connection, reads the request head byte by byte until CRLFCRLF,
reads exactly `Content-Length` bytes and writes the reply itself. `Counts.fs`
counts lines, words and bytes over the raw bytes so UTF-8 never round-trips
through a decoder. `Json.fs` is a small recursive-descent reader that keeps the
text member's bytes, and `Contract.fs` holds the routes, the percent decoder and
the JSON writer.

## Layout

```
{{ npm_name }}.fsproj          single exe project, warnings are errors
src/Counts.fs                  record + counting over byte[]
src/Json.fs                    hand-written JSON reader (escapes, surrogate pairs)
src/Contract.fs                routes, query decoding, JSON replies
src/Server.fs                  TcpListener, head/body reads, reply writer
src/Program.fs                 --selftest, HOST/PORT, exit codes
tests/Tests.fs                 34 checks, no test framework
.github/workflows/ci.yml       build, selftest, HTTP contract
```

## Run

```sh
dotnet build {{ npm_name }}.fsproj --nologo
PORT=8080 dotnet bin/Debug/net8.0/{{ npm_name }}.dll
curl -s 'http://127.0.0.1:8080/stats?text=hello%20world%0A'
```

`GET /health` answers `{"status":"ok"}`. `GET /stats?text=...` and
`POST /stats` with `{"text":"..."}` answer
`{"text":...,"lines":N,"words":N,"bytes":N}`; a missing or non-string member and
a body that is not JSON are 422, an unknown route is 404, a wrong method on a
known route is 405.

## Traps this starter already paid for

- A `while` condition and its `do` must share a line. Splitting them yields
  `FS3122: Missing 'do' in 'while' expression`.
- `TcpListener(...)` as a bare constructor call trips `FS0760` under
  warnings-as-errors; write `new TcpListener(...)`.
- `stream.ReadByte()` returning `-1` is the only end-of-stream signal; a loop
  that ignores it spins forever on a client that hangs up mid-head.
