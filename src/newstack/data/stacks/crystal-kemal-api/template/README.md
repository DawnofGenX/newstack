# {{ title }}

{{ description }}

A [Kemal](https://kemalcr.com) service whose counting rules and entire route table
are plain Crystal functions — `crystal spec` covers every status code without
binding a socket, and the CI job still starts the binary and queries it.

## Run it

```sh
shards install
shards build --release
PORT=8080 ./bin/{{ npm_name }}
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
* **word** — every maximal run of non-space characters.
* **byte** — the UTF-8 byte size, not the character count: `"héllo wörld\n"` is 14
  bytes in 12 characters, which is why the code uses `bytesize` and never `size`.

The rules live in `src/{{ package_name }}/counts.cr`; the route table is
`src/{{ package_name }}/contract.cr` and returns a `Reply` record (status + JSON), so
it is a pure function of `(method, path, query, body)`.

## Layout

```
src/{{ package_name }}/counts.cr    counting rules, no I/O
src/{{ package_name }}/contract.cr  route(method, path, query, body) → Reply
src/{{ package_name }}/server.cr    Kemal routes, each one funnelling into contract
src/{{ package_name }}/main.cr      reads PORT and starts Kemal
spec/                               counting and contract specs (no sockets)
```

## Test

```sh
crystal spec
crystal tool format --check src spec
```
