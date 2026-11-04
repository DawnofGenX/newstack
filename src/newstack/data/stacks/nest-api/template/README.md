# {{ title }}

{{ description }}

A NestJS 12 service on Node {{ node_version }} with three surfaces: `GET /` greets,
`GET /stats?text=...` returns `{lines, words, bytes}` for that text, and a missing
`text` is a 400 rather than a crash. Everything is ESM — NestJS 12 has no CommonJS
build, so `package.json` sets `"type": "module"` and the imports carry `.js` suffixes.

## Layout

`src/main.ts`                  bootstrap, listens on `PORT` (3000 by default)
`src/app.module.ts`            root module
`src/stats/stats.module.ts`    feature module
`src/stats/stats.service.ts`   the counting: newlines, whitespace runs, UTF-8 bytes
`src/stats/stats.controller.ts`the two routes
`src/stats/text-query.pipe.ts` rejects a missing `text` with 400
`test/*.spec.ts`               6 unit tests and 4 end-to-end tests over supertest

## Use

    {{ package_manager_install }}
    PORT=3000 {{ package_manager_run }} start

    curl 'http://localhost:3000/'
    curl 'http://localhost:3000/stats?text=hello%20world'

    $ curl -s 'http://127.0.0.1:3000/stats?text=alpha%20beta%0Agamma%0A'
    {"lines":2,"words":3,"bytes":17}
    $ curl -s -w ' [%{http_code}]' http://127.0.0.1:3000/stats
    {"message":"text is required","error":"Bad Request","statusCode":400} [400]

## Test

    {{ package_manager_run }} typecheck
    {{ package_manager_test }}

    10 tests, 10 passed

## Notes

`jest.config.js` exists for one reason: NodeNext imports end in `.js`, and ts-jest
would look for a JavaScript file that is not there until the project is built, so
the `moduleNameMapper` strips the suffix and jest reads the TypeScript source.
