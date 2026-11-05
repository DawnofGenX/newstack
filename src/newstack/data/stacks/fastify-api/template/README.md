# {{ npm_name }}

A Fastify 5 text-statistics service in TypeScript: one catch-all route, a pure
routing function, `node --test` integration tests, and a live curl contract check.

```bash
npm install
npm run typecheck
npm test          # build + node --test
npm run selftest  # 44 checks, no socket
PORT=8080 npm start
bash smoke.sh     # live contract check on port 5460
```

## Layout

| Path | What it holds |
| --- | --- |
| `src/counts.ts` | `wc` counting over the raw UTF-8 bytes (`countText`) |
| `src/contract.ts` | pure `route({method, target, body}) -> {status, body}` |
| `src/app.ts` | Fastify wiring: content-type parsers, error mapping, one catch-all route |
| `src/selftest.ts` | the offline checks `--selftest` runs |
| `src/main.ts` | PORT/HOST handling, signal drain |
| `tests/contract.test.ts` | integration tests against a server on an ephemeral port |
| `smoke.sh` | starts the service, asserts every route with curl, stops it |

## Routes

| Request | Answer |
| --- | --- |
| `GET /health` | `200 {"status":"ok"}` |
| `GET /stats?text=…` | `200 {"text":…,"lines":N,"words":N,"bytes":N}` |
| `POST /stats {"text":…}` | same body |
| `POST /stats` without `text` | `422 {"error":"missing_text"}` |
| `POST /stats` with broken JSON or a non-string `text` | `422 {"error":"invalid_json"}` |
| other methods on `/health`, `/stats` | `405 {"error":"method_not_allowed"}` |
| anything else | `404 {"error":"not_found","detail":"no route for GET /nope"}` |

## Traps this starter already paid for

- Fastify keeps its built-in JSON parser for `application/json` even after you add a
  `*` parser, so `{}` arrived as an object and the service answered `invalid_json`
  instead of `missing_text`. `app.removeAllContentTypeParsers()` before
  `addContentTypeParser("*", { parseAs: "string" }, …)` is what makes the raw body
  readable, and the raw body is the only way to tell "malformed" from "missing member".
- Fastify answers a body-parser error itself (`400 FST_ERR_CTP_INVALID_JSON`), so a
  `setErrorHandler` has to map parse failures to the 422 the contract promises.
- A response object handed to Fastify goes through its serializer; sending
  `JSON.stringify(reply)` keeps the key order (`text, lines, words, bytes`) fixed.
- `bodyLimit` rejects with `FST_ERR_CTP_BODY_TOO_LARGE`; that must be mapped to 413
  explicitly or it surfaces as a 422.
- `Buffer.from(text, "utf8").length` is the byte count. `text.length` counts UTF-16
  code units and is wrong for anything outside ASCII.
- `engines.node` is enforced by CI only if the runner honours it; the matrix in
  `.github/workflows/ci.yml` is the real gate.
