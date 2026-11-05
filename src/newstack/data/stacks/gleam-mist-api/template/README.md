# {{ title }}

{{ description }}

A small JSON service on [Gleam](https://gleam.io) and [Mist](https://hex.pm/packages/mist).
The counting rules are the usual ones: a line is a newline byte, a word is a maximal run of
non-space characters and `bytes` is the UTF-8 byte size.

## Layout

```
gleam.toml                       project manifest, dependencies and the Erlang target
manifest.toml                    locked dependency versions
src/{{ package_name }}.gleam            Mist server, environment lookup, `main`
src/{{ package_name }}/count.gleam      `count_text` and the `Counts` record
src/{{ package_name }}/contract.gleam   the whole HTTP contract as a pure function
src/{{ package_name }}_env_ffi.erl      `os:getenv/1`, which the stdlib does not bind
test/{{ package_name }}_test.gleam      gleeunit suite
```

`contract.route/4` takes `(method, path, query, body)` and returns a status and a JSON document.
Keeping it pure means the request handling is tested without a socket; the `http` verify step
then checks the same answers over a real one.

## Run it

```sh
gleam deps download
gleam test
PORT=8080 gleam run
```

Rebar3 is needed because one of Mist's transitive dependencies ships as an Erlang package.

## Endpoints

| Request | Answer |
| --- | --- |
| `GET /health` | `200 {"status":"ok"}` |
| `GET /stats?text=hello%20world%0A` | `200 {"text":"hello world\n","lines":1,"words":2,"bytes":12}` |
| `POST /stats` with `{"text":"a b\nc\n"}` | `200 {"text":"a b\nc\n","lines":2,"words":3,"bytes":6}` |
| `GET /stats` without `text` | `422 {"error":"missing_text","detail":"the `text` query parameter is required"}` |
| `POST /stats` with a non-string `text` | `422 {"error":"missing_text","detail":"`text` must be a string"}` |
| `POST /stats` with a body that is not JSON | `422 {"error":"invalid_json",…}` |
| `POST /stats` with a body over 64 KiB | `413 {"error":"body_too_large"}` |
| anything else | `404 {"error":"not_found","detail":"no route for GET /nope"}` |
| a known path with the wrong method | `405 {"error":"method_not_allowed"}` |

The `text` value is counted exactly as sent: nothing is trimmed.

## Reference

- [Gleam language tour](https://tour.gleam.run)
- [Mist documentation](https://hexdocs.pm/mist)
