# {{ title }}

{{ description }}

A GraphQL API on [GraphQL Yoga](https://the-guild.dev/graphql/yoga-server) with a
schema-first SDL: `src/schema.ts` holds the type definitions as a string, `src/resolvers.ts`
holds the functions, and `createSchema()` refuses to start if the two disagree. The
interesting parts are the two guards — a query **depth limit** that turns a cyclic client
into a clean `QUERY_TOO_DEEP` error instead of a hung server, and tests that go through
`yoga.fetch()`, the same handler the socket uses, so nothing is mocked.

This scaffold asks for **Node {{ node_version }} or newer** (`engines` in `package.json`)
and its CI runs every major in the same list.

## Develop

```bash
{{ package_manager_install }}
{{ package_manager_run }} dev      # tsx watch, http://127.0.0.1:5441/graphql
```

Open that URL in a browser for GraphiQL, or post to it:

```bash
curl -s -X POST -H 'content-type: application/json' \
  -d '{"query":"{stats(text:\"hello world\\n\"){lines words bytes}}"}' \
  http://127.0.0.1:5441/graphql
```

## Check

```bash
{{ package_manager_run }} typecheck   # tsc --noEmit
{{ package_manager_test }}            # vitest run
{{ package_manager_run }} build       # tsc -p tsconfig.build.json → dist/
{{ package_manager_run }} start       # node dist/server.js
```

## Schema

```graphql
type Query {
  health: Health!
  stats(text: String!): Stat!
}

type Health {
  status: String!
}

type Stat {
  text: String!
  lines: Int!
  words: Int!
  bytes: Int!
}
```

| Operation | Result |
| --- | --- |
| `{health{status}}` | `{"data":{"health":{"status":"ok"}}}` |
| `{stats(text:"hello world\n"){lines words bytes}}` | `{"data":{"stats":{"lines":1,"words":2,"bytes":12}}}` |
| `{stats(text:42){bytes}}` | `200` with `errors[0].extensions.code == "GRAPHQL_VALIDATION_FAILED"` |
| `{stats{bytes}}` | `200` with `Argument "Query.stats(text:)" of type "String!" is required` |
| `query ($t: String!) {…}` with no variables | `400`, `Expected a value of non-null type "String!" to be provided.` |
| `{a{b{c{d{e{f{g}}}}}}}` | `200` with `extensions.code == "QUERY_TOO_DEEP"` |

That split is worth knowing before you write client code: GraphQL over HTTP answers a
malformed **request** — bad JSON, or a required variable left out — with `400`, but a
malformed **query** — a bad literal, a missing argument, a type error — with `200` and an
`errors` array while `data` is absent. Clients must read `errors`, not just the status code.

Counts are `wc`-compatible: a line is a `\n`, a word is a run of non-whitespace, and bytes
are UTF-8 bytes, so `héllo wörld\n` is 14 bytes, not 12 characters.

## Layout

- `src/stat.ts` — `countText(text)`, a pure function with no Yoga or Node globals.
- `src/schema.ts` — the SDL string. One place to add a field.
- `src/resolvers.ts` — `Query.health` and `Query.stats`; a non-string argument raises
  `BAD_USER_INPUT` rather than returning a half-filled object.
- `src/limits.ts` — `depthOf(document)` and `depthLimit(max)`, a Yoga plugin that reports
  `QUERY_TOO_DEEP` before execution. The limit is 6 selections; fragments are counted at
  their selection set, not inlined, so a pathological fragment chain is caught by the
  execution timeout instead.
- `src/yoga.ts` — `createSchema()` + `createYoga()`: one exported handler, no `listen`.
- `src/server.ts` — the only file that opens a port; reads `PORT` (default `5441`).
- `test/graphql.test.ts` — drives the real handler through `yoga.fetch()`, including the
  depth limit and the 400/200 split above.

After the first `{{ package_manager_install }}`, commit `{{ package_manager_lock }}` and switch
CI's install step to `{{ package_manager_ci }}` for reproducible installs.

Generated with [newstack](https://github.com/DawnofGenX/newstack).
