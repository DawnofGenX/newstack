# {{ project_name }}

A JSON service in OCaml: `Unix` for the socket, the standard library for a
hand-written JSON reader, and dune for the build. No opam package is installed
beyond dune itself.

```console
$ dune build
$ dune runtest
15 passed, 0 failed

$ PORT=8080 ./bin/{{ npm_name }}
listening on http://127.0.0.1:8080
```

## What it counts

Same rules as `wc`: a line is one `'\n'`, a word is a maximal run of non-space
bytes (space, tab, newline, carriage return, vertical tab and form feed all
separate), and bytes are the raw length — so `"héllo wörld\n"` is 1 line, 2
words and 14 bytes, because OCaml `string`s are bytes and never characters.

## Routes

| Method | Path | Answer |
| --- | --- | --- |
| `GET` | `/health` | `{"status":"ok"}` |
| `GET` | `/stats?text=…` | `{"text":…,"lines":…,"words":…,"bytes":…}` |
| `POST` | `/stats` | the same shape, from a `{"text":"…"}` JSON body |

A missing or non-string `text` is `422 missing_text`; a body that is not a JSON
object is `422 invalid_json`, so `{"text":42}` is `missing_text`. A known path
under another method is `405`, a payload over 64 KiB is `413`, and anything else
is a JSON `404` naming the method and path.

## Why the JSON reader is hand-written

`yojson` is usually the answer, but this stack promises no opam packages, so
`lib/json.ml` reads one value and keeps the raw text of numbers: a `42` can
never be confused with `"42"`, which is exactly the distinction the contract
needs. It also decodes `\uXXXX` escapes, including surrogate pairs, so an emoji
survives the round trip. Trailing bytes after the value are a syntax error.

## Layout

| File | Role |
| --- | --- |
| `lib/counts.ml` | `Counts.of_bytes` — counting, no I/O |
| `lib/json.ml` | the reader: `read_text` returns `Text`, `Missing` or `Invalid` |
| `lib/contract.ml` | `route` — pure: method/path/query/body in, status and body out |
| `lib/server.ml` | the socket loop: one request per connection, `SIGPIPE` ignored |
| `bin/main.ml` | reads `HOST`/`PORT` and blocks |
| `test/` | three `dune runtest` suites over a 40-line stdlib harness |

`dune build @all` type-checks everything, and dune's default profile turns the
warnings it enables into errors, so the build step is also the lint gate.
