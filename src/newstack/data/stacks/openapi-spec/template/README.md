# {{ title }}

{{ description }}

The OpenAPI document is the source of truth here, not a description of the code that gets
generated at the end. `openapi.yaml` is written first, linted, bundled and rendered into an
HTML reference, and then the contract tests check that the server's **live responses** match
the schemas it declares. Change a field in the response and the suite fails with

```
AssertionError: response does not match the document: data must NOT have additional properties
```

which is the whole point: a document that nobody validates is worse than no document.

## Commands

```bash
npm install
npm run lint:spec   # spectral, oas ruleset, warnings are failures
npm run bundle      # dist/openapi.yaml — what a client generator consumes
npm run docs        # dist/index.html — the rendered reference
npm test            # bundle, then validate live responses against the document
npm run check       # all of the above in order
npm start           # http://127.0.0.1:5399
```

## What is where

- `openapi.yaml` — OpenAPI **3.1**, so component schemas are JSON Schema 2020-12.
- `.spectral.yaml` — extends `spectral:oas` and turns two of its warnings
  (`operation-description`, `operation-tag-defined`) into errors. `--fail-severity=warn` in
  `package.json` is what makes the other warnings fatal too; neither setting works alone.
- `.redocly.yaml` — names the `recommended` ruleset, so the failures from `redocly lint`
  have a visible origin instead of appearing by default.
- `src/server.js` — a `node:http` server with no runtime dependencies, exporting
  `createApp()` (a handler) and `createHttpServer()`, so tests bind an ephemeral port.
- `test/contract.test.js` — loads `dist/openapi.yaml` (the bundle, not the source, so a
  broken `$ref` cannot survive), compiles each documented response schema with `ajv` in
  2020-12 mode, and asserts every response — including the `422`s and the JSON `404`.

## The rules the contract encodes

- `text` is required. A missing query parameter or a missing body field is a `422` with
  `{"error": "missing_text"}`, never an empty count — a client that forgets the input should
  not receive a plausible-looking zero.
- Text is counted **exactly as sent**. `"  padded  \n"` is 11 bytes, so the document says
  `additionalProperties: false` and the server does no trimming.
- Bytes are UTF-8 bytes, not characters: `"héllo wörld\n"` is 14.
- The `/nope` `404` is not in `paths` — it is the fallback, and the test validates its body
  against the `Error` component directly rather than pretending the document covers it.

Generated with [newstack](https://github.com/DawnofGenX/newstack).
