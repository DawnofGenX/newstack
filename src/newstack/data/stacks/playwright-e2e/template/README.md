# {{ npm_name }}

A Playwright suite that tests a page in a real browser. Playwright starts the fixture
server itself, so one command runs everything; the suite covers typing, byte-vs-character
counting, a `fetch` to the fixture API, label association, a JSON 404 and a phone viewport.

```bash
npm install
npx playwright install chromium   # add --with-deps on a fresh Linux box
npm test                          # playwright test
npx playwright test --project=mobile
npx playwright show-report        # after a failure, with screenshots and traces
bash smoke.sh                     # suite + proves the fixture port is released
```

## Layout

| Path | What it holds |
| --- | --- |
| `playwright.config.ts` | projects (chromium, Pixel 7), the `webServer` that starts the fixture |
| `fixtures/server.mjs` | zero-dependency server: the page, `/api/stats`, `/api/health` |
| `fixtures/app/` | the page under test (`index.html`, `app.js`, `lib/counts.mjs`) |
| `tests/stats.spec.ts` | the suite: UI, network, label association, 404, client route |
| `tests/mobile.spec.ts` | phone viewport: still counts, and nothing overflows horizontally |
| `smoke.sh` | runs the suite and then asserts nothing is still listening on 5464 |

## Traps this starter already paid for

- `webServer` is what makes the suite self-contained. Without it every `page.goto("/")`
  fails with `net::ERR_CONNECTION_REFUSED`, which looks like a browser problem.
- `reuseExistingServer: false` is deliberate: a stale server on the port would serve an
  old page and the suite would pass against code you are not editing.
- The fixture server only serves files under `fixtures/app`, so a module imported as
  `/lib/counts.mjs` is a 404 and the page silently stops updating — every UI assertion
  then fails while the HTML still renders. Keep shared modules inside the served root.
- On Linux CI, `npx playwright install chromium` alone is not enough: the browser needs
  system libraries, so `--with-deps` (or `playwright install-deps`) must run too.
- `test.results`/`playwright-report` are build output: ignore them and upload them as an
  artifact on failure, or the only evidence of a red run is lost with the container.
- A project-level `testMatch` alone does not stop the *desktop* project from collecting
  a mobile-only spec; it then reports as "1 skipped", hiding a green suite behind a skip.
  `testIgnore: /mobile\.spec\.ts/` on the desktop project is the fix.
- `getByLabel("Text")` is the assertion that catches an unassociated `<label>`; a
  `getByTestId` check passes on markup no screen reader can use.
