# {{ project_name }}

A JSON service in C11, on POSIX sockets and the standard library only — no
framework, no dependency to install, and one `make` away from a binary.

```console
$ make
$ make test
all checks passed

$ PORT=8080 ./build/{{ npm_name }}
listening on http://127.0.0.1:8080
```

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
| `src/counters.c` | `textstat_count` — the counting core, no I/O |
| `src/json.c` | a small JSON reader that keeps strings and numbers apart |
| `src/contract.c` | `textstat_route` — pure: method/path/query/body in, status + body out |
| `src/http.c` | the socket loop: one request per connection, 5 s read timeout |
| `src/main.c` | reads `PORT`/`HOST` and blocks |
| `tests/` | a 20-line assertion header and three suites |

`textstat_route` allocates its reply body, so every caller frees it with
`textstat_reply_free`. The contract tests exercise every status code without
opening a socket; the `http` verify step then proves the wire format.

## Why it is safe to extend

`CFLAGS` carries `-Wall -Wextra -Wpedantic -Werror`, so any warning is a build
failure, and the tests run under plain `make test` with no framework to install.
