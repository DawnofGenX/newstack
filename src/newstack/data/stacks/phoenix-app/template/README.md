# {{ title }}

{{ description }}

A Phoenix 1.7 JSON service with no HTML layer: no templates, no assets, no
database, no PubSub. Counting lives in a pure `{{ class_name }}.TextStat` module and the
controller only chooses status codes and JSON shape.

## Layout

```
mix.exs                                         deps: phoenix, plug_cowboy, jason
config/                                         config.exs + one file per Mix env
lib/{{ package_name }}/application.ex                supervision tree: the endpoint
lib/{{ package_name }}/text_stat.ex                  pure line / word / byte counting
lib/{{ package_name }}_web.ex                        router and controller macros
lib/{{ package_name }}_web/endpoint.ex               request id, telemetry, parsers
lib/{{ package_name }}_web/router.ex                 /health, GET and POST /stats
lib/{{ package_name }}_web/controllers/stat_controller.ex
test/                                            ExUnit: counting plus endpoint dispatch
.github/workflows/ci.yml                         format check, tests, live HTTP check
```

## Routes

| Route | Answer |
| --- | --- |
| `GET /health` | `{"status":"ok"}` |
| `GET /stats?text=...` | `{"text":...,"lines":N,"words":N,"bytes":N}` |
| `POST /stats` with `{"text":"..."}` | the same payload |

Matching `wc`, `lines` counts newlines, `words` counts whitespace-separated runs and
`bytes` counts UTF-8 bytes. Text is echoed back exactly as sent. A missing `text`
answers `422` with `{"error":...}`; an unknown route answers `404`.

## Run

```console
$ mix deps.get
$ mix phx.server
$ curl 'http://127.0.0.1:4000/stats?text=hello%20world%0A'
```

`PORT` overrides the listen port (default `4000`).

## Test

```console
$ mix test
$ mix format --check-formatted
```

The endpoint tests dispatch through the real endpoint in-process, so they cover
`Plug.Parsers`, routing and JSON encoding without opening a socket.

## License

MIT — see [LICENSE](LICENSE).
