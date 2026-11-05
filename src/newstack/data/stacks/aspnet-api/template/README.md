# {{ title }}

{{ description }}

A minimal ASP.NET Core 8 JSON API, kept honest by two layers of tests: counting
lives in a pure `TextStat.Of(string)` returning a `Counts` record, and the HTTP
contract is covered by `WebApplicationFactory` — real routing, real model binding,
real JSON, no port and no sleeps.

## Layout

```
{{ npm_name }}.sln                              solution: build and test the whole tree
{{ npm_name }}.csproj                           the web app (net8.0, nullable, warnings as errors)
Program.cs                                      routes: /health, GET /stats, POST /stats
src/Counts.cs                                   line / word / byte record
src/TextStat.cs                                 pure counting, no I/O
tests/                                          xUnit: pure counting + in-memory HTTP tests
.github/workflows/ci.yml                        restore, build, test, live HTTP check on push
```

## Routes

| Route | Answer |
| --- | --- |
| `GET /health` | `{"status":"ok"}` |
| `GET /stats?text=...` | `{"text":...,"lines":N,"words":N,"bytes":N}` |
| `POST /stats` with `{"text":"..."}` | the same payload |

Matching `wc`, `lines` counts newlines (so text without a trailing newline has one
fewer line than you might expect), `words` counts runs of non-whitespace, `bytes`
counts UTF-8 bytes. Text is echoed back exactly as sent — trailing whitespace is
data, and the test suite fails if the framework trims it.

A missing `text` field or query parameter answers `422` with `{"error":...}`;
an unknown route answers `404`.

## Build and test

```console
$ dotnet build --nologo
$ dotnet test --nologo
```

## Run

```console
$ dotnet run --urls http://127.0.0.1:5199
$ curl 'http://127.0.0.1:5199/stats?text=hello%20world%0A'
$ curl -X POST -H 'Content-Type: application/json' -d '{"text":"a b\nc\n"}' \
    http://127.0.0.1:5199/stats
```

## License

MIT — see [LICENSE](LICENSE).
