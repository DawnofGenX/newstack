# {{ title }}

An Angular 22 standalone-component page that counts lines, words and bytes while you
type. Vitest + jsdom for the unit tests (no browser, no Karma), `ng build` for the
bundle, and a zero-dependency static server so the built page can be checked with curl.

```bash
npm install
npm test          # ng test --watch=false (vitest + jsdom)
npm run build     # writes dist/{{ npm_name }}/browser
npm start         # ng serve on http://localhost:4200
bash smoke.sh     # serves the build on port 5461 and asserts it with curl
```

## Layout

| Path | What it holds |
| --- | --- |
| `src/app/stats.ts` | `countText` / `summarize`, the logic the component and the tests share |
| `src/app/app.ts` | the component: `signal` for the text, `computed` for the counts |
| `src/app/app.html` | the template, with `data-testid` hooks for the tests |
| `src/app/stats.spec.ts` | counting rules, including the byte-vs-code-unit case |
| `src/app/app.spec.ts` | component behaviour: render, recalc on input, clear |
| `tools/serve.mjs` | static server for `dist/<project>/browser` with SPA fallback |
| `smoke.sh` | builds if needed, serves, asserts index/bundle/fallback/404 |

## Traps this starter already paid for

- Angular 22 scaffolds Vitest with jsdom, not Karma, so `ng test` needs no browser and
  no `ChromeHeadless` flag in CI. A scaffold from an older major keeps Karma and will
  hang on a machine without Chrome — do not copy the `test` target blindly.
- `ng build` writes `dist/<project>/browser`; the `<project>` part is the key in
  `angular.json`, not the `package.json` name. Rename one and the static path breaks.
- The script tag `ng build` emits is relative (`src="main-XXXX.js"`), so anything that
  fetches bundle URLs must add the leading slash. `curl http://host:port:main-…` fails
  with "Port number was not a decimal number".
- A single-page app served by a plain static server answers 404 for client routes;
  `tools/serve.mjs` falls back to `index.html` only for paths without a file extension,
  so a stale bundle URL still reports 404 instead of pretending to be a page.
- `TextEncoder().encode(text).length` is the byte count. `text.length` counts UTF-16
  code units: `"héllo wörld\n"` is 12 characters but 14 bytes.
- `signal` + `computed` recompute on every keystroke with no manual subscription; keep
  the counting function pure so the component stays untestable-proof.
- `(input)="update($any($event.target).value)"` — the `$any` cast is what keeps strict
  templates happy without loosening `tsconfig.json`.
