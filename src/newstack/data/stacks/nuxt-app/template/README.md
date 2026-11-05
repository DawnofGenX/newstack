# {{ title }}

A Nuxt 4 app that counts lines, words and UTF-8 bytes. The counter lives in
`lib/counts.ts`, the page is server-rendered, and `server/api/stats.ts` exposes the
same function as JSON so the build can be checked with curl.

```bash
npm install
npm test          # vitest, no browser
npm run build     # nitro server build in .output/
npm start         # node .output/server/index.mjs on $PORT (default 3000)
bash smoke.sh     # builds on port 5465 and asserts SSR, the API and the 404/405 rules
```

## Layout

| Path | What it holds |
| --- | --- |
| `lib/counts.ts` | `stats(text)` — the single counting rule the page, the API and the tests share |
| `pages/index.vue` | the SSR page; without a `pages/` directory Nuxt renders `app.vue` for *every* path and nothing is ever a 404 |
| `server/api/stats.ts` | one file for every method, returning `422 missing_text` / `405` itself |
| `tests/counts.test.ts` | the counting rules, including byte-vs-code-unit |
| `smoke.sh` | build, serve, then curl the page, the API, a 405 and a 404 |
