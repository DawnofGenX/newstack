# {{ npm_name }}

A JSON service that counts lines, words and bytes, in Tcl. It is the newstack
`tcl-http-api` starter: plain `tclsh`, no packages, no build step.

## What it gives you

    POST /stats  {"text": "hello world\n"}
    -> 200 {"text":"hello world\n","lines":1,"words":2,"bytes":12}

| Route | Answer |
| --- | --- |
| `GET /health` | `200 {"status":"ok"}` |
| `GET /stats?text=...` | `200` with the counts, `422 {"error":"missing_text"}` when `text` is absent |
| `POST /stats` | same counts from a JSON body; `422 invalid_json` for a body that is not JSON, `422 missing_text` when `text` is missing or not a string |
| another method on `/health` or `/stats` | `405 {"error":"method_not_allowed"}` |
| anything else | `404 {"error":"not_found","detail":"no route for METHOD /path"}` |

Counting rules are the same ones `wc` uses: a line is a `\n`, a word is a
maximal run of non-space characters, bytes are UTF-8 bytes (so `héllo wörld\n`
is 1 line, 2 words and 14 bytes). The body is counted exactly as sent — no
trimming, no newline appended.

## What is here

    bin/{{ npm_name }}    the server: reads HOST and PORT, then binds
    src/json.tcl       a small strict JSON reader (objects of scalars only)
    src/counts.tcl     the counting core
    src/contract.tcl   method + path + query + body -> status and body, no socket
    src/server.tcl     the socket: reads a request, calls the contract, writes
    tests/run.tcl      24 checks, no tcltest, no socket

The contract is a plain function of four strings, so every status code is tested
without opening a port. `src/server.tcl` is the only file that knows about
sockets, and `tests/run.tcl` never binds anything.

`tclsh` ships with no JSON package on a stock Debian/Ubuntu box (tcllib is a
separate install), which is why the reader is here rather than a dependency.
It keeps numbers and strings apart — `{"text": 42}` is a `422 missing_text`,
not text `42` — and rejects arrays and trailing data instead of half-parsing
them.

## Getting started

    tclsh tests/run.tcl
    PORT=8080 ./bin/{{ npm_name }}

Then:

    curl 'http://127.0.0.1:8080/stats?text=hello%20world%0A'
    curl -X POST -H 'content-type: application/json' \
         --data-binary '{"text":"a b\nc\n"}' http://127.0.0.1:8080/stats

`HOST` defaults to `127.0.0.1` and `PORT` to `8080`.
