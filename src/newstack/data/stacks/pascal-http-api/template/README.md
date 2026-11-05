# blog-count

A JSON service in Free Pascal: the listener comes from fcl-web, everything else
— counting, JSON, the whole HTTP contract — is plain code you can call from a
test without opening a socket.

```sh
make            # builds build/blog-count
make test       # 58 checks, no test framework
PORT=8080 ./bin/blog-count
```

`HOST` (default `127.0.0.1`) and `PORT` (default `8080`) are read from the
environment. On Debian/Ubuntu the listener needs the `fp-units-fcl` package
next to `fpc`.

## Routes

| Method | Path | Answers |
| --- | --- | --- |
| `GET` | `/health` | `{"status":"ok"}` |
| `GET` | `/stats?text=…` | `{"text":"…","lines":1,"words":2,"bytes":12}` |
| `POST` | `/stats` | the same shape, for `{"text": "…"}` |
| any | `/health`, `/stats` | `405` `{"error":"method_not_allowed"}` |
| any | anything else | `404` `{"error":"not_found","detail":"no route for GET /nope"}` |

Missing text answers `422 {"error":"missing_text"}`; a body that is not JSON, or
a `text` that is not a string (`{"text": 42}`), also answers `422` — the first
as `invalid_json`, the second as `missing_text`. Counting follows `wc`: a line
ends at `\n`, a word is a maximal run of non-space characters, and bytes are
UTF-8 bytes (`"héllo wörld\n"` is 1 line, 2 words, 14 bytes). The body is
counted exactly as sent, so `"  padded  \n"` keeps its padding.

## Layout

| Path | What it holds |
| --- | --- |
| `src/counts.pas` | the counting rules, no HTTP |
| `src/jsonbody.pas` | a JSON reader that keeps a number apart from a string |
| `src/contract.pas` | `Route(method, path, query, body)`, the whole contract as one pure function |
| `src/server.pas` | `TFPHTTPServer` glue |
| `src/app.pas` | `HOST`/`PORT`, then the accept loop |
| `tests/run_tests.pas` | plain `Check()` calls; the exit code is the gate |

## Two things worth knowing

`fpjson` is deliberately not used. It hands strings back in the system codepage,
so `\u00e9` arrives as ONE latin-1 byte instead of two UTF-8 bytes, and a
surrogate pair (`\ud83d\ude42`) turns into two question marks — both would make
the byte count wrong. The reader here decodes escapes into UTF-8 itself, and
rejects trailing rubbish after the object.

`fpc -o` and `-Fu` take no space after the flag (`-obuild/app`,
`-Fusrc`); `-o build/app` is read as a stray source file and fails with
`Error: Illegal parameter: -o`.
