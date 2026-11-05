# {{ title }}

{{ description }}

A JSON API on [Hono](https://hono.dev) and Node, deliberately without a bundler: `tsc`
emits plain ESM into `dist/`, and `node dist/server.js` serves it. `hono` is small enough
that the interesting part is the testing story — `createApp()` returns the app as a value,
so every route test calls `app.request("/stats?text=…")` and gets a real `Response` back
in-process. No port, no `afterAll` teardown, no flaky waits.

This scaffold asks for **Node {{ node_version }} or newer** (`engines` in `package.json`)
and its CI runs every major in the same list.

## Develop

```bash
{{ package_manager_install }}
{{ package_manager_run }} dev      # tsx watch, http://127.0.0.1:3000
```

## Check

```bash
{{ package_manager_run }} typecheck   # tsc --noEmit
{{ package_manager_test }}            # vitest run
{{ package_manager_run }} build       # tsc -p tsconfig.build.json → dist/
{{ package_manager_run }} start       # node dist/server.js
```

## Endpoints

| Request | Response |
| --- | --- |
| `GET /health` | `{"status":"ok"}` |
| `GET /stats?text=hello%20world%0A` | `{"text":"hello world\n","lines":1,"words":2,"bytes":12}` |
| `POST /stats` with `{"text":"a b\nc\n"}` | `{"text":"a b\nc\n","lines":2,"words":3,"bytes":6}` |
| `POST /stats` without a string `text` | `422` |
| anything else | `404` with `{"error":"not_found"}` |

Counts are `wc`-compatible: a line is a `\n`, a word is a run of non-whitespace, and bytes
are UTF-8 bytes, so `héllo wörld\n` is 14 bytes, not 12 characters.

## Layout

- `src/stat.ts` — `countText(text)`, a pure function with no Hono or Node globals.
- `src/app.ts` — `createApp()`: `/health`, `GET /stats`, `POST /stats`, a JSON `notFound`.
  A missing field, a non-string and a non-JSON body are all `422`, never `500`.
- `src/server.ts` — the only file that opens a port; reads `PORT` (default `3000`).
- `test/app.test.ts` — drives the app through `app.request()`, including the 422/404 paths.

After the first `{{ package_manager_install }}`, commit `{{ package_manager_lock }}` and switch
CI's install step to `{{ package_manager_ci }}` for reproducible installs.

Generated with [newstack](https://github.com/DawnofGenX/newstack).
