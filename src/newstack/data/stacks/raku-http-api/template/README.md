# {{ npm_name }}

A JSON service that counts lines, words and bytes, in Raku. It is the newstack
`raku-http-api` starter: Rakudo, its own `IO::Socket::INET`, and no installs.

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
is 1 line, 2 words and 14 bytes). The body is counted exactly as sent.

## What is here

    bin/{{ npm_name }}    the server: reads HOST and PORT, then binds
    lib/Counts.rakumod   the counting core, over Buf bytes
    lib/Json.rakumod     a strict JSON reader (no JSON::Fast, no JSON::Tiny)
    lib/Contract.rakumod method + path + query + body -> status and body
    lib/Server.rakumod   the socket: read a request, call the contract, write
    t/run.raku           48 checks, Rakudo's own Test module, no socket

The contract is a plain function of four strings, so every status code is tested
without opening a port. `lib/Server.rakumod` is the only file that knows about
sockets, and `t/run.raku` never binds anything.

Rakudo ships no JSON parser and no `zef` on a stock install, so the reader is
here rather than a dependency. It keeps numbers and strings apart — `{"text":
42}` is a `422 missing_text`, not text `42` — and rejects arrays and trailing
data instead of half-parsing them.

## Traps this starter already paid for

- A literal space inside a character class is ignored by Raku's regex engine, so
  `/^<[ \t\n\r]>$/` matches a tab but never a space. Write `\x20`:
  `/^<[\x20\t\n\r]>$/`. This one silently broke request-head parsing.
- `"\x0bb"` reads as hex `0xBB`, because a hex escape takes three digits when it
  can. Use `"\x[0b]"` and `"\x[0c]"` for vertical tab and form feed.
- Between scalars, `eq` is the right test; but `my int $mark = $text.index('?')`
  dies with `Cannot unbox a type object (Nil) to int` when there is no `?`. Keep
  the result in a `my $mark` and guard with `with $mark { ... }`.
- `raku -c lib/Foo.rakumod` needs `-Ilib` too, or it dies `Could not find Counts`.

## Getting started

    raku -Ilib t/run.raku
    PORT=8080 ./bin/{{ npm_name }}

Then:

    curl 'http://127.0.0.1:8080/stats?text=hello%20world%0A'
    curl -X POST -H 'content-type: application/json' \
         --data-binary '{"text":"a b\nc\n"}' http://127.0.0.1:8080/stats

`HOST` defaults to `127.0.0.1` and `PORT` to `8080`.
