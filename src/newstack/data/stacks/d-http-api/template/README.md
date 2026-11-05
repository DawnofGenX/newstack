# {{ project_name }}

A JSON service in D, compiled with LDC: `std.socket` for the wire, the standard
library for everything else, and no package manager in sight.

```console
$ make
$ make test
all checks passed

$ PORT=8080 ./build/{{ npm_name }}
listening on http://127.0.0.1:8080
```

## What it counts

Same rules as `wc`: a line is one `'\n'`, a word is a maximal run of non-space
characters (space, tab, newline, carriage return, vertical tab and form feed all
separate), and bytes are the UTF-8 payload — so `"héllo wörld\n"` is 1 line, 2
words and 14 bytes while a `string` in D is already bytes, so `text.length` is
the byte count and no encoder is needed.

## Routes

| Method | Path | Answer |
| --- | --- | --- |
| `GET` | `/health` | `{"status":"ok"}` |
| `GET` | `/stats?text=…` | `{"text":…,"lines":…,"words":…,"bytes":…}` |
| `POST` | `/stats` | the same shape, from a `{"text":"…"}` JSON body |

A missing or non-string `text` is `422 missing_text`; a body that is not a JSON
object is `422 invalid_json` — `{"text":42}` is `missing_text`, because a number
is not text. A known path under another method is `405`, a payload over 64 KiB is
`413`, and anything else is a JSON `404` naming the method and path.

`std.json` stops at the end of the first value, so bytes after the object are
ignored rather than rejected; the tests pin that behaviour instead of pretending
otherwise.

## Layout

| File | Role |
| --- | --- |
| `source/textstat/counts.d` | `countText` — counting over the UTF-8 payload, no I/O |
| `source/textstat/json.d` | `readText` — `std.json`, keeping a string distinct from a number |
| `source/textstat/contract.d` | `route` — pure: method/path/query/body in, status and body out |
| `source/textstat/server.d` | the socket loop: one request per connection, `SIGPIPE` ignored |
| `source/app.d` | reads `PORT`/`HOST` and blocks |
| `test/runtests.d` | pulls in the modules so `-unittest` runs every `unittest` block |

The tests are ordinary D `unittest` blocks compiled with `-unittest -main`, so
there is no test framework to install; `-w -de` in `DFLAGS` makes a deprecation
or a warning a build failure.
