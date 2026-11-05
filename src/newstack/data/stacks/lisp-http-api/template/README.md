# {{ project_name }}

A JSON service in Common Lisp. SBCL ships `sb-bsd-sockets`, so the whole service —
counting, the route table, the JSON reader and the HTTP loop — is standard library
only, with no Quicklisp and nothing to install.

```console
$ sbcl --script tests/run-tests.lisp
checks: 32, passed: 32, failed: 0

$ PORT=8080 ./bin/{{ npm_name }}
listening on http://127.0.0.1:8080
```

## What it counts

Same rules as `wc`: a line is one `#\Newline`, a word is a maximal run of non-space
characters (space, tab, newline, return, vertical tab and form feed all separate),
and bytes are the UTF-8 encoding — so `"héllo wörld\n"` is 1 line, 2 words and 14
bytes. Text is counted exactly as it arrives: nothing is trimmed.

## Routes

| Method | Path | Answer |
| --- | --- | --- |
| `GET` | `/health` | `{"status":"ok"}` |
| `GET` | `/stats?text=…` | `{"text":…,"lines":…,"words":…,"bytes":…}` |
| `POST` | `/stats` | the same shape, from a `{"text":"…"}` JSON body |

A missing or non-string `text` is `422 missing_text`; a body that is not JSON is
`422 invalid_json`; a known path under another method is `405`; anything else is a
JSON `404` whose detail names the method and path.

## Layout

| File | Role |
| --- | --- |
| `lib/counts.lisp` | `count-text` — the counting core, no I/O |
| `lib/json.lisp` | a small JSON reader that keeps strings and numbers apart |
| `lib/contract.lisp` | `route` — pure: `(method path query body)` in, `(status body)` out |
| `lib/server.lisp` | the socket loop, one thread per connection |
| `main.lisp` | reads `PORT`/`HOST` and blocks |
| `bin/{{ npm_name }}` | wrapper: `sbcl --script`, so there is no build step |
| `tests/run-tests.lisp` | 32 checks over the counting core, the JSON reader and every route |

`route` is pure and knows nothing about sockets, so the tests exercise every status
code without binding a port; the `http` verify step then proves the wire format.
