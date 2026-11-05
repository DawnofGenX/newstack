# {{ title }}

{{ description }}

A Julia JSON service on [HTTP.jl](https://juliapackages.com/p/http): counting
lines, words and bytes the way `wc` does, exposed over `GET /health`,
`GET /stats` and `POST /stats`. Counting lives in a pure function
(`TextstatApi.count_text`), the whole route table is another pure function
(`TextstatApi.route`), and `src/main.jl` is the only file that touches a socket
— so the test suite drives every status code directly and only one test needs
a real port.

## Layout

```
Project.toml              package metadata, HTTP + JSON3 and their UUIDs
src/TextstatApi.jl        module; includes counts.jl and contract.jl
src/counts.jl             Counts value type and pure count_text(text)
src/contract.jl           Reply, query_param and the pure route(method, path, query, body)
src/main.jl               HTTP.serve(handler, host, port); reads PORT and ADDR
test/runtests.jl          Test suite: counting table, every route, one socket case
```

## Endpoints

| Request | Answer |
| --- | --- |
| `GET /health` | `200 {"status":"ok"}` |
| `GET /stats?text=...` | `200 {"text":...,"lines":N,"words":N,"bytes":N}`, `422 {"error":"missing_text"}` without the parameter |
| `POST /stats` with `{"text": "..."}` | the same `200`, `422 {"error":"missing_text"}` for a missing or non-string `text`, `422 {"error":"invalid_json"}` for a body that is not a JSON object |
| `DELETE /health`, `PUT /stats` | `405 {"error":"method_not_allowed"}` |
| anything else | `404 {"error":"not_found","detail":"no route for METHOD /path"}` |

A line ends at `\n`, a word is a maximal run of non-whitespace characters, and
bytes are the UTF-8 encoding — `"héllo wörld\n"` is 1 line, 2 words and 14 bytes
even though it has 12 characters.

## Notes

- The package name is fixed as `TextstatApi` (and so is its UUID) because a Julia
  module name has to be an identifier; see the comment at the top of
  `Project.toml` if you want to rename it.
- `Manifest.toml` is gitignored, so the first `Pkg.instantiate()` resolves
  HTTP 1.x and JSON3 1.x from the General registry. Commit it instead if you
  want byte-for-byte reproducible builds.
- `Pkg.instantiate()` downloads and precompiles about 18 packages once; after
  that the suite runs in well under a second.
