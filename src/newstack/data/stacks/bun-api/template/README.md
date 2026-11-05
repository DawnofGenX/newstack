# {{ title }}

A JSON service in Bun with no framework. `handler` is a plain
`(Request) => Promise<Response>` function, `Bun.serve` accepts it as `fetch`, and `bun test`
calls it with constructed requests — no port, no flakiness.

## Requirements

- Bun 1.1 or newer (`bun --version`)
- `curl`, for the smoke test

## Layout

```
package.json         scripts and dev dependencies (`bun-types` is the registry marker)
tsconfig.json        strict, noEmit — types are checked by `bun run typecheck`
src/count.ts         counting rules, no HTTP
src/handler.ts       handler(): routing and JSON
src/server.ts        Bun.serve({ port, hostname, fetch: handler })
test/count.test.ts   the counting table
test/handler.test.ts the routes, driven in-process
```

## Run it

```sh
bun install
bun test
PORT=8080 bun run src/server.ts

curl 'http://127.0.0.1:8080/health'
curl 'http://127.0.0.1:8080/stats?text=hello%20world%0A'
curl -X POST -H 'content-type: application/json' \
     --data-binary '{"text":"a b\nc\n"}' http://127.0.0.1:8080/stats
```

`GET /stats` returns the counted text plus `lines`, `words` and `bytes`. A missing `text`
parameter is a `422`, an unparseable body is a `422` (never a `500`), an unknown path is a
JSON `404`, and a method the route does not implement is a `405`.

Counting matches `wc`: a line ends at `\n`, a word is a maximal run of non-space characters,
`bytes` is the UTF-8 length — `héllo` is 5 characters and 6 bytes.

## Test it

```sh
bun test
bun run typecheck
```

`bun test` runs the `bun:test` suite in `test/`. Both suites call `handler` directly, so the
fast path needs no socket; the verify manifest still boots the real server, because an
in-process handler can hide a binding or startup problem.

## Gates

- `bun test` — the unit and route suites
- `bun run typecheck` — `tsc --noEmit` over `src` and `test` with `bun-types` loaded
- live `curl` assertions against a booted server

## Notes

- `Bun.env` reads `PORT` and `ADDR` (default `127.0.0.1:8080`).
- `bun install` writes `bun.lock`; commit it so deploys resolve the same versions. The template
  ships without one.
- `server.stop(true)` on `SIGINT`/`SIGTERM` closes in-flight requests before the process exits.
