# {{ title }}

{{ description }}

A Nim service that counts lines, words and bytes, built on `std/asynchttpserver`
with no third-party dependencies: `nimble build` needs no network access.

## Run it

```sh
nimble build
PORT=8080 ./{{ package_name }}
```

```sh
curl 'http://127.0.0.1:8080/stats?text=hello%20world%0A'
# {"text":"hello world\n","lines":1,"words":2,"bytes":12}
```

## Endpoints

| request | answer |
| --- | --- |
| `GET /health` | `{"status":"ok"}` |
| `GET /stats?text=…` | `{"text", "lines", "words", "bytes"}`; missing `text` → 422 `missing_text` |
| `POST /stats` with `{"text": "…"}` | the same body; missing or non-string `text` → 422, a body that is not a JSON object → 422 `invalid_json` |
| anything else | 404 `not_found` with a `detail` naming the method and path |

## Counting rules

* **line** — every `\n` byte, so a file ending in a newline has no extra empty line.
* **word** — every maximal run of non-space bytes (`isspace` is `' '`, `\t`, `\n`,
  `\r`, `\v`, `\f`).
* **byte** — the length of the UTF-8 encoding, not the number of characters:
  `"héllo wörld\n"` is 14 bytes in 12 characters.

The rules live in `src/counts.nim`, so the CLI and the service can never drift.

## Layout

```
src/counts.nim      counting rules, no I/O
src/app.nim         the whole contract as one pure function: route(method, path, query, body)
src/server.nim      adapts an asynchttpserver request to route()
src/{{ package_name }}.nim   the binary: reads PORT, serves forever
tests/test_all.nim  unittest for the rules and the router (no sockets)
```

Because the router is a pure function, `nimble test` covers every status code and
body without opening a port; the CI job then starts the real binary and queries it.

## Test

```sh
nimble test
nim check --hints:off src/{{ package_name }}.nim
```
