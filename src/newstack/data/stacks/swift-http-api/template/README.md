# {{ project_name }}

A JSON service in Swift 6 on POSIX sockets and the standard library only — no
package manifest, no dependency to resolve, and one `make` away from a binary.

```console
$ make
$ make test
checks: 34, passed: 34, failed: 0

$ PORT=8080 ./build/{{ npm_name }}
listening on http://127.0.0.1:8080
```

`make` invokes `swiftc` directly instead of `swift build`, because a service this
size needs no package graph: one command, one binary, and `-warnings-as-errors`
keeps the build honest.

## What it counts

Same rules as `wc`: a line is one `'\n'`, a word is a maximal run of non-space
bytes (space, tab, newline, carriage return, vertical tab and form feed all
separate), and bytes are the UTF-8 encoding — so `"héllo wörld\n"` is 1 line, 2
words and 14 bytes. Text is counted exactly as it arrives: nothing is trimmed.

## Routes

| Method | Path | Answer |
| --- | --- | --- |
| `GET` | `/health` | `{"status":"ok"}` |
| `GET` | `/stats?text=…` | `{"text":…,"lines":…,"words":…,"bytes":…}` |
| `POST` | `/stats` | the same shape, from a `{"text":"…"}` JSON body |

A missing or non-string `text` is `422 missing_text`; a body that is not a JSON
object is `422 invalid_json` — so `{"text":42}` is `missing_text`, because a number
is not text. A known path under another method is `405`, a payload over 64 KiB is
`413`, and anything else is a JSON `404` whose detail names the method and path.

## Layout

| File | Role |
| --- | --- |
| `src/Counts.swift` | `Counts.of` — the counting core, no I/O |
| `src/JsonBody.swift` | a JSON reader that keeps strings and numbers apart |
| `src/Contract.swift` | `Contract.route` — pure: method/path/query/body in, reply out |
| `src/Server.swift` | the socket loop: one request per connection, `SO_REUSEADDR` |
| `src/main.swift` | reads `PORT`/`HOST`, runs `--selftest` or blocks |
| `tests/Tests.swift` | 34 checks, compiled into the binary and run by `--selftest` |

The contract is a pure function, so the whole status-code matrix — 200, 404, 405,
413, 422 — is exercised in `make test` without opening a socket; the `http` verify
step then proves the wire format on a real port.

## Two Swift details worth knowing

`String.UTF8View` is indexed by `String.Index`, not by `Int`, so the JSON scanner
decodes into `Array(raw.utf8)` first and walks integers — an escape sequence is
then just `index += 3`.

Sending through a pointer into a `[UInt8]` element (`&out[sent]`) reads the array's
buffer, not the bytes: the first live run answered `HTTP/0.9` because curl got
metadata. Copy the response into a local array and send inside
`withUnsafeBufferPointer`; the same holds for `recv` and `withUnsafeMutableBufferPointer`.

## Why it is safe to extend

`swiftc -warnings-as-errors` means any warning is a build failure, and `make test`
needs no test framework to install — the harness is 40 lines in `tests/Tests.swift`.
