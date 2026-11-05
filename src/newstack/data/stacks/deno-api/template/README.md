# {{ title }}

A JSON service in Deno with no framework. One function — `(Request) => Response` — is the whole
application, `Deno.serve` turns it into a server, and a test can call it with a constructed
request.

## Requirements

- Deno 2 (`deno --version`)
- `curl`, for the smoke test

## Layout

```
deno.json            dependencies, tasks, and the entry the registry detects
src/count.ts         counting rules — no HTTP in sight
src/handler.ts       handler(): routing and JSON, Request in, Response out
src/server.ts        Deno.serve({ port, hostname }, handler)
test/count_test.ts   the counting table
test/handler_test.ts the routes, driven in-process
```

## Run it

```sh
deno task test
PORT=8080 deno task start

curl 'http://127.0.0.1:8080/health'
curl 'http://127.0.0.1:8080/stats?text=hello%20world%0A'
curl -X POST -H 'content-type: application/json' \
     --data-binary '{"text":"a b\nc\n"}' http://127.0.0.1:8080/stats
```

`GET /stats` returns the text it counted plus `lines`, `words` and `bytes`. A missing `text`
parameter is a `422`, an unparseable body is a `422` (not a `500`), an unknown path is a JSON
`404`, and a method the route does not implement is a `405`.

Counting matches `wc`: a line ends at `\n`, a word is a maximal run of non-space characters,
`bytes` is the UTF-8 length — `héllo` is 5 characters and 6 bytes.

## Test it

```sh
deno test --allow-env --allow-net
```

`handler` is a plain function, so the tests build `Request` objects and await the `Response`.
No port is opened and nothing can flake. The verify step still boots the real server over a
socket, because an in-process-only handler can hide a binding or permission problem.

## Gates

```sh
deno check src/handler.ts src/server.ts   # types, including the std dependency
deno fmt --check src test                 # formatting is enforced, not suggested
deno lint src test
```

`deno run` needs `--allow-env` (for `PORT`) and `--allow-net` (to bind). Nothing else is
granted, so the service cannot read the filesystem even if a dependency tries to.

## Notes

- `deno.json` pins the std modules through `imports`; `@std/assert` is the only test dependency.
- The template ships no lock file. A service should commit `deno.lock` after the first
  `deno task test` so deploys use the resolved versions.
