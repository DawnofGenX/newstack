# {{ title }}

{{ description }}

A Mojolicious JSON service in Perl 5 that counts lines, words and bytes the way
`wc` does. Counting lives in `Textstat::Counts`, the whole route table and every
status code live in `Textstat::Contract` (a pure function of method, path, query
and body), and `bin/{{ npm_name }}` only talks to the socket.

## Endpoints

| Method | Path | Answer |
| --- | --- | --- |
| `GET` | `/health` | `200 {"status":"ok"}` |
| `GET` | `/stats?text=...` | `200 {"text","lines","words","bytes"}`, `422 {"error":"missing_text"}` when `text` is absent |
| `POST` | `/stats` with `{"text": "..."}` | same body as `GET`; `422 {"error":"missing_text"}` for a non-string `text`, `422 {"error":"invalid_json"}` for a body that is not one JSON object |
| any | a known path with another method | `405 {"error":"method_not_allowed"}` |
| any | anything else | `404 {"error":"not_found","detail":"no route for METHOD /path"}` |

The text is counted exactly as sent: `"  padded  \n"` is one line, one word and
eleven bytes, and a trailing newline is a line of its own.

## Why the JSON round trip

`JSON::PP` decodes `42` and `"42"` into values that both stringify to `42`, so a
numeric `text` would sneak through a plain `defined` check. `Textstat::Contract`
therefore re-encodes the decoded value: a string comes back quoted and a number
does not, which is how `{"text": 42}` is answered with `422 missing_text`.

## Running it

```sh
perl Makefile.PL
make test
PORT=8080 perl bin/{{ npm_name }}
curl 'http://127.0.0.1:8080/stats?text=hello%20world%0A'
```

## Layout

```
Makefile.PL                  ExtUtils::MakeMaker build script (NAME, EXE_FILES, tests)
cpanfile                     the runtime dependency list (Mojolicious, JSON::PP)
bin/{{ npm_name }}           the only file that binds a port and writes bytes
lib/Textstat/Counts.pm       line / word / byte value object plus pure counting
lib/Textstat/Contract.pm     the route table: status codes and JSON bodies
t/01-counts.t                the counting table
t/02-contract.t              every branch of the route table
```

`{{ package_name }}`-style module names are deliberately not used: Perl module
names cannot carry hyphens, so this stack keeps the fixed `Textstat` namespace
even when the project directory is named something else.
