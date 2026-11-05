# {{ title }}

A JSON service in Zig. `zig build` produces `zig-out/bin/{{ npm_name }}`, `zig build test`
runs every unit test, and the server speaks the same wc-style contract as our
other service starters.

## What it does

| Route | Method | Answer |
| --- | --- | --- |
| `/health` | `GET` | `{"status":"ok"}` |
| `/stats` | `GET` | counts for `?text=`, `422 {"error":"missing_text"}` when the parameter is absent |
| `/stats` | `POST` | counts for `{"text": "..."}`; `422 {"error":"invalid_json"}` for a body that is not JSON, `422 {"error":"missing_text"}` when `text` is missing or not a string |
| anything else | any | `404 {"error":"not_found","detail":"no route for METHOD /path"}` |
| a known path, wrong method | any | `405 {"error":"method_not_allowed"}` |

Counting follows `wc`: a line is one `\n` byte (so a final line without a
newline is not counted), a word is a maximal run of non-whitespace, and bytes are
the raw UTF-8 length — `héllo` is 5 characters but 6 bytes.

```
GET /stats?text=hello%20world%0A
{"text":"hello world\n","lines":1,"words":2,"bytes":12}
```

The text is counted exactly as sent: no trimming, no normalising, no newline
mending. That is why the JSON above reports 12 bytes for 11 characters plus one
newline.

## Layout

| File | Job |
| --- | --- |
| `src/main.zig` | process wiring: read `PORT`/`ADDR`, bind, serve |
| `src/server.zig` | the socket layer — accept, parse the head, reply |
| `src/contract.zig` | pure routing and JSON rendering; every answer is decided here |
| `src/counting.zig` | pure counting: lines, words, bytes |
| `build.zig` | the executable plus one test binary per module |

`server.zig` is the only file that touches a socket, `contract.zig` and
`counting.zig` are pure functions, so the test suite covers every status code
without opening a port.

## Running it

```sh
zig build
PORT=8080 ./zig-out/bin/{{ npm_name }}
zig build test
zig fmt --check build.zig src
```

`PORT` defaults to 8080 and `ADDR` to `127.0.0.1`; the service prints
`listening on http://...` once it is bound.

## Zig 0.17 notes

- `main` takes `std.process.Init`, which carries the `Io` handle and the
  environment map — there is no global allocator or ambient I/O any more.
- `std.http.Server.init` wants `Io.Reader`/`Io.Writer` interfaces, so
  `server.zig` owns the read/write buffers and hands over their `.interface`
  pointers.
- A request body is read with `request.readerExpectNone(buffer)` — the server
  does not decode chunked or compressed bodies, and this starter does not ask
  for them.
- `build.zig.zon` ships one fixed package identity (`.textstat`). Zig ties the
  fingerprint to crc32 of the name *and* the absolute path of the project, so a
  scaffolded project cannot compute its own value. If you publish this under
  your own name, change `.name`, delete `.fingerprint`, run `zig build`, and
  paste the suggested value back in.
- Each connection answers exactly one request and closes; the reply carries
  `connection: close`. That keeps the loop simple and is what the test suite
  expects.

## License

MIT — see `LICENSE`.
